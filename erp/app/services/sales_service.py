from datetime import date as date_type
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.sales import SalesOrder, SalesOrderLine, SaleInvoice, SaleInvoiceLine, Receipt
from app.models.master_data import Contact, Product, ChartOfAccount
from app.models.accounting import Journal
from app.models.enums import DocumentStatus, PaymentStatus, PartyType
from app.services.numbering_service import next_number
from app.services.master_data_service import get_active_or_404
from app.services.accounting_service import post_journal_entry
from app.services.audit_service import log_action


def _resolve_lines(db: Session, raw_lines, price_field: str):
    """Validates products and computes server-side totals; never trusts client totals."""
    if not raw_lines:
        raise HTTPException(status_code=422, detail="At least one line is required")
    resolved = []
    grand_total = Decimal("0")
    for raw in raw_lines:
        product = get_active_or_404(db, Product, raw.product_id)
        qty = Decimal(raw.quantity)
        if qty <= 0:
            raise HTTPException(status_code=422, detail="Quantity must be positive")
        unit_price = Decimal(raw.unit_price) if raw.unit_price is not None else getattr(product, price_field)
        if unit_price < 0:
            raise HTTPException(status_code=422, detail="Unit price cannot be negative")
        tax_rate = Decimal(raw.tax_rate) if raw.tax_rate is not None else product.tax_rate
        if tax_rate < 0:
            raise HTTPException(status_code=422, detail="Tax rate cannot be negative")
        line_total = (qty * unit_price) * (Decimal("1") + tax_rate / Decimal("100"))
        line_total = line_total.quantize(Decimal("0.01"))
        grand_total += line_total
        resolved.append(dict(
            product_id=product.id, quantity=qty, unit_price=unit_price,
            tax_rate=tax_rate, line_total=line_total,
        ))
    return resolved, grand_total.quantize(Decimal("0.01"))


def create_sales_order(db: Session, payload, user_id: int) -> SalesOrder:
    contact = get_active_or_404(db, Contact, payload.contact_id)
    if contact.party_type not in (PartyType.CUSTOMER, PartyType.BOTH):
        raise HTTPException(status_code=422, detail="Selected contact is not a customer")
    lines, total = _resolve_lines(db, payload.lines, "sales_price")

    order = SalesOrder(
        order_number=next_number(db, "SO"),
        contact_id=contact.id,
        order_date=date_type.fromisoformat(payload.order_date),
        status=DocumentStatus.DRAFT,
        total_amount=total,
        created_by_id=user_id,
    )
    for line in lines:
        order.lines.append(SalesOrderLine(**line))
    db.add(order)
    log_action(db, user_id, "CREATE", "SalesOrder", None, details=order.order_number)
    db.commit()
    db.refresh(order)
    return order


def confirm_sales_order(db: Session, order_id: int, user_id: int) -> SalesOrder:
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if order.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=422, detail=f"Cannot confirm an order in status {order.status.value}")
    order.status = DocumentStatus.CONFIRMED
    log_action(db, user_id, "CONFIRM", "SalesOrder", order.id)
    db.commit()
    db.refresh(order)
    return order


def _receivable_account_for(db: Session, contact: Contact) -> int:
    if contact.receivable_account_id:
        return contact.receivable_account_id
    default = db.query(ChartOfAccount).filter(ChartOfAccount.code == "1200").first()
    if not default:
        raise HTTPException(status_code=422, detail="No receivable account configured for this contact")
    return default.id


def create_sale_invoice(db: Session, payload, user_id: int) -> SaleInvoice:
    contact = get_active_or_404(db, Contact, payload.contact_id)

    source_order = None
    if payload.sales_order_id:
        source_order = db.query(SalesOrder).filter(SalesOrder.id == payload.sales_order_id).first()
        if not source_order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        if source_order.status != DocumentStatus.CONFIRMED:
            raise HTTPException(status_code=422, detail="Only a confirmed sales order can be invoiced")
        existing = db.query(SaleInvoice).filter(SaleInvoice.sales_order_id == source_order.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="This sales order has already been invoiced")

    if payload.lines:
        lines, total = _resolve_lines(db, payload.lines, "sales_price")
    elif source_order:
        lines = [dict(
            product_id=l.product_id, quantity=l.quantity, unit_price=l.unit_price,
            tax_rate=l.tax_rate, line_total=l.line_total,
        ) for l in source_order.lines]
        total = source_order.total_amount
    else:
        raise HTTPException(status_code=422, detail="At least one line is required")

    invoice = SaleInvoice(
        invoice_number=next_number(db, "INV"),
        contact_id=contact.id,
        sales_order_id=source_order.id if source_order else None,
        invoice_date=date_type.fromisoformat(payload.invoice_date),
        status=DocumentStatus.DRAFT,
        payment_status=PaymentStatus.UNPAID,
        total_amount=total,
        created_by_id=user_id,
    )
    for line in lines:
        invoice.lines.append(SaleInvoiceLine(**line))
    db.add(invoice)
    log_action(db, user_id, "CREATE", "SaleInvoice", None, details=invoice.invoice_number)
    db.commit()
    db.refresh(invoice)
    return invoice


def confirm_sale_invoice(db: Session, invoice_id: int, user_id: int) -> SaleInvoice:
    invoice = db.query(SaleInvoice).filter(SaleInvoice.id == invoice_id).with_for_update().first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    if invoice.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=422, detail=f"Cannot confirm an invoice in status {invoice.status.value}")

    contact = db.query(Contact).filter(Contact.id == invoice.contact_id).first()
    receivable_account_id = _receivable_account_for(db, contact)
    sales_journal = db.query(Journal).filter(Journal.code == "SALES").first()
    if not sales_journal:
        raise HTTPException(status_code=422, detail="Sales journal (code=SALES) is not configured")

    je_lines = [dict(account_id=receivable_account_id, debit=invoice.total_amount, credit=0,
                      description=f"Receivable for {invoice.invoice_number}")]
    remaining = invoice.total_amount
    for line in invoice.lines:
        product = db.query(Product).filter(Product.id == line.product_id).first()
        income_account_id = product.income_account_id
        if not income_account_id:
            default_income = db.query(ChartOfAccount).filter(ChartOfAccount.code == "4000").first()
            if not default_income:
                raise HTTPException(status_code=422, detail="No income account configured")
            income_account_id = default_income.id
        je_lines.append(dict(account_id=income_account_id, debit=0, credit=line.line_total,
                              description=f"Sale of {product.name}"))

    post_journal_entry(
        db, journal_id=sales_journal.id, entry_date=invoice.invoice_date, lines=je_lines,
        narration=f"Sale invoice {invoice.invoice_number}",
        source_type="SaleInvoice", source_id=invoice.id,
    )

    invoice.status = DocumentStatus.CONFIRMED
    log_action(db, user_id, "CONFIRM", "SaleInvoice", invoice.id)
    db.commit()
    db.refresh(invoice)
    return invoice


def record_receipt(db: Session, payload, user_id: int) -> Receipt:
    if payload.idempotency_key:
        existing = db.query(Receipt).filter(Receipt.idempotency_key == payload.idempotency_key).first()
        if existing:
            return existing  # duplicate submission returns the original result, doesn't double-process

    invoice = db.query(SaleInvoice).filter(SaleInvoice.id == payload.sale_invoice_id).with_for_update().first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Sale invoice not found")
    if invoice.status != DocumentStatus.CONFIRMED:
        raise HTTPException(status_code=422, detail="Only a confirmed invoice can receive payment")

    amount = Decimal(payload.amount)
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be positive")

    outstanding = invoice.total_amount - invoice.amount_paid
    if amount > outstanding:
        raise HTTPException(status_code=422, detail=f"Amount exceeds outstanding balance of {outstanding}")

    receipt = Receipt(
        receipt_number=next_number(db, "RCPT"),
        sale_invoice_id=invoice.id,
        contact_id=invoice.contact_id,  # payment contact is forced to match the invoice's contact
        amount=amount,
        receipt_date=date_type.fromisoformat(payload.receipt_date),
        status=DocumentStatus.CONFIRMED,
        idempotency_key=payload.idempotency_key,
        created_by_id=user_id,
    )
    db.add(receipt)

    invoice.amount_paid += amount
    invoice.payment_status = (
        PaymentStatus.PAID if invoice.amount_paid >= invoice.total_amount else PaymentStatus.PARTIALLY_PAID
    )

    # Post cash/bank receipt accounting: Dr Cash/Bank, Cr Accounts Receivable
    contact = db.query(Contact).filter(Contact.id == invoice.contact_id).first()
    receivable_account_id = _receivable_account_for(db, contact)
    cash_account = db.query(ChartOfAccount).filter(ChartOfAccount.code == "1000").first()
    if not cash_account:
        raise HTTPException(status_code=422, detail="No cash/bank account (code=1000) configured")
    receipts_journal = db.query(Journal).filter(Journal.code == "RECEIPTS").first()
    if not receipts_journal:
        raise HTTPException(status_code=422, detail="Receipts journal (code=RECEIPTS) is not configured")

    db.flush()  # ensure receipt.id is available for the source reference
    post_journal_entry(
        db, journal_id=receipts_journal.id, entry_date=receipt.receipt_date,
        lines=[
            dict(account_id=cash_account.id, debit=amount, credit=0, description="Cash received"),
            dict(account_id=receivable_account_id, debit=0, credit=amount, description="Receivable settled"),
        ],
        narration=f"Receipt {receipt.receipt_number} against {invoice.invoice_number}",
        source_type="Receipt", source_id=receipt.id,
    )

    log_action(db, user_id, "CREATE", "Receipt", None, details=receipt.receipt_number)
    db.commit()
    db.refresh(receipt)
    return receipt
