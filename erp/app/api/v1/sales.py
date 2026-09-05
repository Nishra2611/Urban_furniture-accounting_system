from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin, require_admin
from app.models.user import User
from app.schemas.transactions import SalesOrderCreate, SaleInvoiceCreate, ReceiptCreate
from app.schemas.master_data import BulkIDsReq
from app.services import sales_service as svc
from app.services import master_data_service as master_svc

from app.models.sales import SalesOrder, SaleInvoice, Receipt

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


@router.get("/orders")
def list_orders(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    orders = db.query(SalesOrder).all()
    return [{
        "id": o.id,
        "number": o.order_number,
        "order_number": o.order_number,
        "contact_id": o.contact_id,
        "customer_id": o.contact_id,
        "order_date": o.order_date.isoformat(),
        "status": o.status.value.lower(),
        "total": float(o.total_amount),
        "total_amount": str(o.total_amount),
    } for o in orders]


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


@router.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    return master_svc.delete_record(db, SalesOrder, order_id)


@router.post("/orders/bulk-delete")
def bulk_delete_orders(payload: BulkIDsReq, db: Session = Depends(get_db),
                        _: User = Depends(require_admin)):
    return master_svc.bulk_delete(db, SalesOrder, payload.ids)


@router.get("/invoices")
def list_invoices(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    invoices = db.query(SaleInvoice).all()
    return [{
        "id": i.id,
        "number": i.invoice_number,
        "invoice_number": i.invoice_number,
        "contact_id": i.contact_id,
        "customer_id": i.contact_id,
        "invoice_date": i.invoice_date.isoformat(),
        "status": i.status.value.lower(),
        "payment_status": i.payment_status.value.lower(),
        "total": float(i.total_amount),
        "total_amount": str(i.total_amount),
        "amount_paid": float(i.amount_paid),
    } for i in invoices]


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


@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    return master_svc.delete_record(db, SaleInvoice, invoice_id)


@router.post("/invoices/bulk-delete")
def bulk_delete_invoices(payload: BulkIDsReq, db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    return master_svc.bulk_delete(db, SaleInvoice, payload.ids)


@router.get("/receipts")
def list_receipts(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    receipts = db.query(Receipt).all()
    return [{
        "id": r.id,
        "number": r.receipt_number,
        "receipt_number": r.receipt_number,
        "contact_id": r.contact_id,
        "sale_invoice_id": r.sale_invoice_id,
        "payment_date": r.receipt_date.isoformat(),
        "receipt_date": r.receipt_date.isoformat(),
        "payment_type": "receipt",
        "method": "bank",
        "amount": float(r.amount),
        "status": r.status.value.lower(),
    } for r in receipts]


@router.post("/receipts", status_code=201)
def create_receipt(payload: ReceiptCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant_or_admin)):
    receipt = svc.record_receipt(db, payload, user.id)
    return {"id": receipt.id, "receipt_number": receipt.receipt_number, "amount": str(receipt.amount)}


@router.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    return master_svc.delete_record(db, Receipt, receipt_id)


@router.post("/receipts/bulk-delete")
def bulk_delete_receipts(payload: BulkIDsReq, db: Session = Depends(get_db),
                         _: User = Depends(require_admin)):
    return master_svc.bulk_delete(db, Receipt, payload.ids)
