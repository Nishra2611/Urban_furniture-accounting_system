from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.schemas.transactions import PurchaseOrderCreate, PurchaseBillCreate, VendorPaymentCreate
from app.services import purchase_service as svc

router = APIRouter(prefix="/api/v1/purchase", tags=["purchase"])


@router.post("/orders", status_code=201)
def create_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db),
                  user: User = Depends(require_accountant_or_admin)):
    order = svc.create_purchase_order(db, payload, user.id)
    return {"id": order.id, "order_number": order.order_number, "status": order.status.value,
            "total_amount": str(order.total_amount)}


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_accountant_or_admin)):
    order = svc.confirm_purchase_order(db, order_id, user.id)
    return {"id": order.id, "status": order.status.value}


@router.post("/bills", status_code=201)
def create_bill(payload: PurchaseBillCreate, db: Session = Depends(get_db),
                 user: User = Depends(require_accountant_or_admin)):
    bill = svc.create_purchase_bill(db, payload, user.id)
    return {"id": bill.id, "bill_number": bill.bill_number, "status": bill.status.value,
            "total_amount": str(bill.total_amount)}


@router.post("/bills/{bill_id}/confirm")
def confirm_bill(bill_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_accountant_or_admin)):
    bill = svc.confirm_purchase_bill(db, bill_id, user.id)
    return {"id": bill.id, "status": bill.status.value}


@router.post("/payments", status_code=201)
def create_payment(payload: VendorPaymentCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant_or_admin)):
    payment = svc.record_vendor_payment(db, payload, user.id)
    return {"id": payment.id, "payment_number": payment.payment_number, "amount": str(payment.amount)}
