"""The restricted User-role portal: own invoices/bills only, payment status, and pay-dues action.

Data ownership is enforced at the query level (filtered by contact_id tied to the
authenticated user), not merely hidden in the UI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.sales import SaleInvoice
from app.schemas.transactions import ReceiptCreate
from app.services import sales_service as svc

router = APIRouter(prefix="/api/v1/portal", tags=["user-portal"])


def _require_linked_contact(user: User) -> int:
    if not user.contact_id:
        raise HTTPException(status_code=422, detail="No customer account is linked to this login")
    return user.contact_id


@router.get("/my-invoices")
def my_invoices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contact_id = _require_linked_contact(user)
    invoices = db.query(SaleInvoice).filter(SaleInvoice.contact_id == contact_id).all()
    return [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "invoice_date": i.invoice_date.isoformat(),
            "total_amount": str(i.total_amount),
            "amount_paid": str(i.amount_paid),
            "payment_status": i.payment_status.value,
        }
        for i in invoices
    ]


@router.post("/pay")
def pay_invoice(payload: ReceiptCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    contact_id = _require_linked_contact(user)
    invoice = db.query(SaleInvoice).filter(SaleInvoice.id == payload.sale_invoice_id).first()
    if not invoice or invoice.contact_id != contact_id:
        # Never reveal another customer's invoice, even by ID guess.
        raise HTTPException(status_code=404, detail="Invoice not found")
    receipt = svc.record_receipt(db, payload, user.id)
    return {"id": receipt.id, "receipt_number": receipt.receipt_number, "amount": str(receipt.amount)}
