from datetime import date as date_type
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.purchase import PurchaseOrder, PurchaseOrderLine, PurchaseBill, PurchaseBillLine, VendorPayment
from app.models.master_data import Contact, Product, ChartOfAccount
from app.models.accounting import Journal
from app.models.enums import DocumentStatus, PaymentStatus, PartyType
from app.services.numbering_service import next_number
from app.services.master_data_service import get_active_or_404
from app.services.accounting_service import post_journal_entry
from app.services.audit_service import log_action
from app.services.sales_service import _resolve_lines  # reuse the same server-side line resolution


def _payable_account_for(db: Session, contact: Contact) -> int:
    if contact.payable_account_id:
        return contact.payable_account_id
    default = db.query(ChartOfAccount).filter(ChartOfAccount.code == "2000").first()
    if not default:
        raise HTTPException(status_code=422, detail="No payable account configured for this contact")
    return default.id


def create_purchase_order(db: Session, payload, user_id: int) -> PurchaseOrder:
    contact = get_active_or_404(db, Contact, payload.contact_id)
    if contact.party_type not in (PartyType.VENDOR, PartyType.BOTH):
        raise HTTPException(status_code=422, detail="Selected contact is not a vendor")
    lines, total = _resolve_lines(db, payload.lines, "purchase_price")

    order = PurchaseOrder(
        order_number=next_number(db, "PO"),
        contact_id=contact.id,
        order_date=date_type.fromisoformat(payload.order_date),
        status=DocumentStatus.DRAFT,
        total_amount=total,
        created_by_id=user_id,
    )
    for line in lines:
        order.lines.append(PurchaseOrderLine(**line))
    db.add(order)
    log_action(db, user_id, "CREATE", "PurchaseOrder", None, details=order.order_number)
    db.commit()
    db.refresh(order)
    return order


def confirm_purchase_order(db: Session, order_id: int, user_id: int) -> PurchaseOrder:
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=422, detail=f"Cannot confirm an order in status {order.status.value}")
    order.status = DocumentStatus.CONFIRMED
    log_action(db, user_id, "CONFIRM", "PurchaseOrder", order.id)
    db.commit()
    db.refresh(order)
    return order


def create_purchase_bill(db: Session, payload, user_id: int) -> PurchaseBill:
    contact = get_active_or_404(db, Contact, payload.contact_id)

    source_order = None
    if payload.purchase_order_id:
        source_order = db.query(PurchaseOrder).filter(PurchaseOrder.id == payload.purchase_order_id).first()
        if not source_order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        if source_order.status != DocumentStatus.CONFIRMED:
            raise HTTPException(status_code=422, detail="Only a confirmed purchase order can be billed")
        existing = db.query(PurchaseBill).filter(PurchaseBill.purchase_order_id == source_order.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="This purchase order has already been billed")

    if payload.lines:
        lines, total = _resolve_lines(db, payload.lines, "purchase_price")
    elif source_order:
        lines = [dict(
            product_id=l.product_id, quantity=l.quantity, unit_price=l.unit_price,
            tax_rate=l.tax_rate, line_total=l.line_total,
        ) for l in source_order.lines]
        total = source_order.total_amount
    else:
        raise HTTPException(status_code=422, detail="At least one line is required")

    bill = PurchaseBill(
        bill_number=next_number(db, "BILL"),
        contact_id=contact.id,
        purchase_order_id=source_order.id if source_order else None,
        bill_date=date_type.fromisoformat(payload.bill_date),
        status=DocumentStatus.DRAFT,
        payment_status=PaymentStatus.UNPAID,
        total_amount=total,
        created_by_id=user_id,
    )
    for line in lines:
        bill.lines.append(PurchaseBillLine(**line))
    db.add(bill)
    log_action(db, user_id, "CREATE", "PurchaseBill", None, details=bill.bill_number)
    db.commit()
    db.refresh(bill)
    return bill


def confirm_purchase_bill(db: Session, bill_id: int, user_id: int) -> PurchaseBill:
    bill = db.query(PurchaseBill).filter(PurchaseBill.id == bill_id).with_for_update().first()
    if not bill:
        raise HTTPException(status_code=404, detail="Purchase bill not found")
    if bill.status != DocumentStatus.DRAFT:
        raise HTTPException(status_code=422, detail=f"Cannot confirm a bill in status {bill.status.value}")

    contact = db.query(Contact).filter(Contact.id == bill.contact_id).first()
    payable_account_id = _payable_account_for(db, contact)
    purchase_journal = db.query(Journal).filter(Journal.code == "PURCHASE").first()
    if not purchase_journal:
        raise HTTPException(status_code=422, detail="Purchase journal (code=PURCHASE) is not configured")

    je_lines = [dict(account_id=payable_account_id, debit=0, credit=bill.total_amount,
                      description=f"Payable for {bill.bill_number}")]
    for line in bill.lines:
        product = db.query(Product).filter(Product.id == line.product_id).first()
        expense_account_id = product.expense_account_id
        if not expense_account_id:
            default_expense = db.query(ChartOfAccount).filter(ChartOfAccount.code == "5000").first()
            if not default_expense:
                raise HTTPException(status_code=422, detail="No expense account configured")
            expense_account_id = default_expense.id
        je_lines.append(dict(account_id=expense_account_id, debit=line.line_total, credit=0,
                              description=f"Purchase of {product.name}"))

    post_journal_entry(
        db, journal_id=purchase_journal.id, entry_date=bill.bill_date, lines=je_lines,
        narration=f"Purchase bill {bill.bill_number}",
        source_type="PurchaseBill", source_id=bill.id,
    )

    bill.status = DocumentStatus.CONFIRMED
    log_action(db, user_id, "CONFIRM", "PurchaseBill", bill.id)
    db.commit()
    db.refresh(bill)
    return bill


def record_vendor_payment(db: Session, payload, user_id: int) -> VendorPayment:
    if payload.idempotency_key:
        existing = db.query(VendorPayment).filter(
            VendorPayment.idempotency_key == payload.idempotency_key
        ).first()
        if existing:
            return existing

    bill = db.query(PurchaseBill).filter(PurchaseBill.id == payload.purchase_bill_id).with_for_update().first()
    if not bill:
        raise HTTPException(status_code=404, detail="Purchase bill not found")
    if bill.status != DocumentStatus.CONFIRMED:
        raise HTTPException(status_code=422, detail="Only a confirmed bill can be paid")

    amount = Decimal(payload.amount)
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Amount must be positive")

    outstanding = bill.total_amount - bill.amount_paid
    if amount > outstanding:
        raise HTTPException(status_code=422, detail=f"Amount exceeds outstanding balance of {outstanding}")

    payment = VendorPayment(
        payment_number=next_number(db, "PAY"),
        purchase_bill_id=bill.id,
        contact_id=bill.contact_id,
        amount=amount,
        payment_date=date_type.fromisoformat(payload.payment_date),
        status=DocumentStatus.CONFIRMED,
        idempotency_key=payload.idempotency_key,
        created_by_id=user_id,
    )
    db.add(payment)

    bill.amount_paid += amount
    bill.payment_status = (
        PaymentStatus.PAID if bill.amount_paid >= bill.total_amount else PaymentStatus.PARTIALLY_PAID
    )

    contact = db.query(Contact).filter(Contact.id == bill.contact_id).first()
    payable_account_id = _payable_account_for(db, contact)
    cash_account = db.query(ChartOfAccount).filter(ChartOfAccount.code == "1000").first()
    if not cash_account:
        raise HTTPException(status_code=422, detail="No cash/bank account (code=1000) configured")
    payments_journal = db.query(Journal).filter(Journal.code == "PAYMENTS").first()
    if not payments_journal:
        raise HTTPException(status_code=422, detail="Payments journal (code=PAYMENTS) is not configured")

    db.flush()
    post_journal_entry(
        db, journal_id=payments_journal.id, entry_date=payment.payment_date,
        lines=[
            dict(account_id=payable_account_id, debit=amount, credit=0, description="Payable settled"),
            dict(account_id=cash_account.id, debit=0, credit=amount, description="Cash paid"),
        ],
        narration=f"Payment {payment.payment_number} against {bill.bill_number}",
        source_type="VendorPayment", source_id=payment.id,
    )

    log_action(db, user_id, "CREATE", "VendorPayment", None, details=payment.payment_number)
    db.commit()
    db.refresh(payment)
    return payment
