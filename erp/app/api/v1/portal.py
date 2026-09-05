"""The restricted User-role portal: own invoices/bills only, payment status, and pay-dues action.

Data ownership is enforced at the query level (filtered by contact_id tied to the
authenticated user), not merely hidden in the UI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_contact_user
from app.models.user import User
from app.models.sales import SaleInvoice, Receipt
from app.models.purchase import PurchaseBill, VendorPayment
from app.schemas.transactions import ReceiptCreate, VendorPaymentCreate
from app.services import purchase_service as purchase_svc
from app.services import sales_service as svc

router = APIRouter(prefix="/api/v1/portal", tags=["user-portal"])


def _require_linked_contact(user: User) -> int:
    if not user.contact_id:
        raise HTTPException(status_code=422, detail="No customer account is linked to this login")
    return user.contact_id


@router.get("/my-invoices")
def my_invoices(db: Session = Depends(get_db), user: User = Depends(require_contact_user)):
    contact_id = _require_linked_contact(user)
    invoices = db.query(SaleInvoice).filter(SaleInvoice.contact_id == contact_id).all()
    return [
        {
            "id": i.id,
            "number": i.invoice_number,
            "invoice_number": i.invoice_number,
            "invoice_date": i.invoice_date.isoformat(),
            "status": i.status.value.lower(),
            "total": float(i.total_amount),
            "amount_paid": float(i.amount_paid),
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
            "bill_date": b.bill_date.isoformat(),
            "status": b.status.value.lower(),
            "total": float(b.total_amount),
            "amount_paid": float(b.amount_paid),
            "payment_status": b.payment_status.value,
        }
        for b in bills
    ]


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
