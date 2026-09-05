from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.schemas.transactions import SalesOrderCreate, SaleInvoiceCreate, ReceiptCreate
from app.services import sales_service as svc

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


@router.post("/orders", status_code=201)
def create_order(payload: SalesOrderCreate, db: Session = Depends(get_db),
                  user: User = Depends(require_accountant_or_admin)):
    order = svc.create_sales_order(db, payload, user.id)
    return {"id": order.id, "order_number": order.order_number, "status": order.status.value,
            "total_amount": str(order.total_amount)}


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_accountant_or_admin)):
    order = svc.confirm_sales_order(db, order_id, user.id)
    return {"id": order.id, "status": order.status.value}


@router.post("/invoices", status_code=201)
def create_invoice(payload: SaleInvoiceCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant_or_admin)):
    invoice = svc.create_sale_invoice(db, payload, user.id)
    return {"id": invoice.id, "invoice_number": invoice.invoice_number, "status": invoice.status.value,
            "total_amount": str(invoice.total_amount)}


@router.post("/invoices/{invoice_id}/confirm")
def confirm_invoice(invoice_id: int, db: Session = Depends(get_db),
                     user: User = Depends(require_accountant_or_admin)):
    invoice = svc.confirm_sale_invoice(db, invoice_id, user.id)
    return {"id": invoice.id, "status": invoice.status.value}


@router.post("/receipts", status_code=201)
def create_receipt(payload: ReceiptCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant_or_admin)):
    receipt = svc.record_receipt(db, payload, user.id)
    return {"id": receipt.id, "receipt_number": receipt.receipt_number, "amount": str(receipt.amount)}
