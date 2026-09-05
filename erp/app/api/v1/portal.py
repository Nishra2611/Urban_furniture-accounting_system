"""The restricted User-role portal: own invoices/bills only, payment status, and pay-dues action.

Data ownership is enforced at the query level (filtered by contact_id tied to the
authenticated user), not merely hidden in the UI.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.core.deps import require_contact_user
from app.models.user import User
from app.models.sales import SaleInvoice, Receipt, SaleInvoiceLine
from app.models.purchase import PurchaseBill, VendorPayment, PurchaseBillLine
from app.models.master_data import Contact, Product
from app.schemas.transactions import ReceiptCreate, VendorPaymentCreate
from app.services import purchase_service as purchase_svc
from app.services import sales_service as svc

router = APIRouter(prefix="/api/v1/portal", tags=["user-portal"])


def _require_linked_contact(user: User) -> int:
    if not user.contact_id:
        raise HTTPException(status_code=422, detail="No customer account is linked to this login")
    return user.contact_id


def _due_date(value):
    return (value + timedelta(days=30)).isoformat()


def _status(document, today=None):
    due = document.amount_paid < document.total_amount
    if due and today and today > document.invoice_date if hasattr(document, "invoice_date") else False:
        return "overdue"
    return document.status.value.lower()


def _invoice_payload(invoice, contact, payments=None, lines=None):
    return {
        "id": invoice.id, "number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(), "due_date": _due_date(invoice.invoice_date),
        "status": invoice.status.value.lower(), "payment_status": invoice.payment_status.value,
        "total": float(invoice.total_amount), "amount_paid": float(invoice.amount_paid),
        "amount_due": float(invoice.total_amount - invoice.amount_paid),
        "contact": {"name": contact.name, "email": contact.email, "phone": contact.phone, "address": contact.address} if contact else None,
        "lines": lines or [], "payments": payments or [],
    }


@router.get("/my-invoices")
def my_invoices(db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    invoices = db.query(SaleInvoice).filter(SaleInvoice.contact_id == contact_id).all()
    return [
        {
            "id": i.id,
            "number": i.invoice_number,
            "invoice_number": i.invoice_number,
            "invoice_date": i.invoice_date.isoformat(), "due_date": _due_date(i.invoice_date),
            "status": i.status.value.lower(),
            "total": float(i.total_amount),
            "amount_paid": float(i.amount_paid),
            "amount_due": float(i.total_amount - i.amount_paid),
            "total_amount": str(i.total_amount),
            "payment_status": i.payment_status.value,
        }
        for i in invoices
    ]


@router.get("/my-bills")
def my_bills(db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    bills = db.query(PurchaseBill).filter(PurchaseBill.contact_id == contact_id).all()
    return [
        {
            "id": b.id,
            "number": b.bill_number,
            "bill_number": b.bill_number,
            "bill_date": b.bill_date.isoformat(), "due_date": _due_date(b.bill_date),
            "status": b.status.value.lower(),
            "total": float(b.total_amount),
            "amount_paid": float(b.amount_paid),
            "amount_due": float(b.total_amount - b.amount_paid),
            "payment_status": b.payment_status.value,
        }
        for b in bills
    ]


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    invoices = db.query(SaleInvoice).filter(SaleInvoice.contact_id == contact_id).all()
    bills = db.query(PurchaseBill).filter(PurchaseBill.contact_id == contact_id).all()
    payments = [*db.query(Receipt).filter(Receipt.contact_id == contact_id).all(),
                *db.query(VendorPayment).filter(VendorPayment.contact_id == contact_id).all()]
    outstanding = sum((d.total_amount - d.amount_paid for d in [*invoices, *bills]), 0)
    total_paid = sum((p.amount for p in payments), 0)
    month = __import__("datetime").date.today().replace(day=1)
    paid_month = sum((p.amount for p in payments if (p.receipt_date if hasattr(p, "receipt_date") else p.payment_date) >= month), 0)
    invoice_rows = [dict(id=i.id, number=i.invoice_number, date=i.invoice_date.isoformat(), total=float(i.total_amount), paid=float(i.amount_paid), due=float(i.total_amount-i.amount_paid), status=i.payment_status.value) for i in invoices]
    bill_rows = [dict(id=b.id, number=b.bill_number, date=b.bill_date.isoformat(), total=float(b.total_amount), paid=float(b.amount_paid), due=float(b.total_amount-b.amount_paid), status=b.payment_status.value) for b in bills]
    return {"outstanding": float(outstanding), "overdue": 0.0, "paid_this_month": float(paid_month),
            "total_paid": float(total_paid), "invoices": invoice_rows[-5:], "bills": bill_rows[-5:],
            "payments": [{"id": p.id, "number": getattr(p, "receipt_number", None) or getattr(p, "payment_number", None), "date": p.receipt_date.isoformat() if hasattr(p, "receipt_date") else p.payment_date.isoformat(), "amount": float(p.amount), "status": p.status.value} for p in payments[-5:]]}


@router.get("/invoices/{invoice_id}")
def invoice_detail(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    invoice = db.query(SaleInvoice).filter(SaleInvoice.id == invoice_id, SaleInvoice.contact_id == contact_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    lines = []
    for line in invoice.lines:
        product = db.query(Product).filter(Product.id == line.product_id).first()
        lines.append({"product": product.name if product else "-", "quantity": float(line.quantity), "unit_price": float(line.unit_price), "tax_rate": float(line.tax_rate), "line_total": float(line.line_total)})
    payments = [{"number": r.receipt_number, "date": r.receipt_date.isoformat(), "amount": float(r.amount), "status": r.status.value} for r in db.query(Receipt).filter(Receipt.sale_invoice_id == invoice.id).all()]
    return _invoice_payload(invoice, contact, payments, lines)


@router.get("/bills/{bill_id}")
def bill_detail(bill_id: int, db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    bill = db.query(PurchaseBill).filter(PurchaseBill.id == bill_id, PurchaseBill.contact_id == contact_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    lines = []
    for line in bill.lines:
        product = db.query(Product).filter(Product.id == line.product_id).first()
        lines.append({"product": product.name if product else "-", "quantity": float(line.quantity), "unit_price": float(line.unit_price), "tax_rate": float(line.tax_rate), "line_total": float(line.line_total)})
    payments = [{"number": p.payment_number, "date": p.payment_date.isoformat(), "amount": float(p.amount), "status": p.status.value} for p in db.query(VendorPayment).filter(VendorPayment.purchase_bill_id == bill.id).all()]
    return {"id": bill.id, "number": bill.bill_number, "bill_date": bill.bill_date.isoformat(), "due_date": _due_date(bill.bill_date), "status": bill.status.value.lower(), "payment_status": bill.payment_status.value, "total": float(bill.total_amount), "amount_paid": float(bill.amount_paid), "amount_due": float(bill.total_amount-bill.amount_paid), "contact": {"name": contact.name, "email": contact.email, "phone": contact.phone, "address": contact.address} if contact else None, "lines": lines, "payments": payments}


@router.get("/my-payments")
def my_payments(db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    receipts = db.query(Receipt).filter(Receipt.contact_id == contact_id).all()
    payments = db.query(VendorPayment).filter(VendorPayment.contact_id == contact_id).all()
    return [
        {
            "id": r.id, "number": r.receipt_number, "payment_type": "receipt",
            "payment_date": r.receipt_date.isoformat(), "amount": float(r.amount), "method": "bank",
        }
        for r in receipts
    ] + [
        {
            "id": p.id, "number": p.payment_number, "payment_type": "payment",
            "payment_date": p.payment_date.isoformat(), "amount": float(p.amount), "method": "bank",
        }
        for p in payments
    ]


@router.post("/pay")
def pay_invoice(payload: ReceiptCreate, db: Session = Depends(get_db),
                user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    invoice = db.query(SaleInvoice).filter(SaleInvoice.id == payload.sale_invoice_id).first()
    if not invoice or invoice.contact_id != contact_id:
        # Never reveal another customer's invoice, even by ID guess.
        raise HTTPException(status_code=404, detail="Invoice not found")
    receipt = svc.record_receipt(db, payload, user.id)
    return {"id": receipt.id, "receipt_number": receipt.receipt_number, "amount": str(receipt.amount)}


@router.post("/pay-bill")
def pay_bill(payload: VendorPaymentCreate, db: Session = Depends(get_db),
             user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    bill = db.query(PurchaseBill).filter(PurchaseBill.id == payload.purchase_bill_id).first()
    if not bill or bill.contact_id != contact_id:
        raise HTTPException(status_code=404, detail="Bill not found")
    payment = purchase_svc.record_vendor_payment(db, payload, user.id)
    return {"id": payment.id, "payment_number": payment.payment_number, "amount": str(payment.amount)}
