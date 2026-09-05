from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.schemas.transactions import PurchaseOrderCreate, PurchaseBillCreate, VendorPaymentCreate
from app.services import purchase_service as svc

from app.models.purchase import PurchaseOrder, PurchaseBill, VendorPayment

router = APIRouter(prefix="/api/v1/purchase", tags=["purchase"])


@router.get("/orders")
def list_orders(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    orders = db.query(PurchaseOrder).all()
    return [{
        "id": o.id,
        "number": o.order_number,
        "order_number": o.order_number,
        "contact_id": o.contact_id,
        "vendor_id": o.contact_id,
        "order_date": o.order_date.isoformat(),
        "status": o.status.value.lower(),
        "total": float(o.total_amount),
        "total_amount": str(o.total_amount),
    } for o in orders]


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


@router.get("/bills")
def list_bills(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    bills = db.query(PurchaseBill).all()
    return [{
        "id": b.id,
        "number": b.bill_number,
        "bill_number": b.bill_number,
        "contact_id": b.contact_id,
        "vendor_id": b.contact_id,
        "bill_date": b.bill_date.isoformat(),
        "status": b.status.value.lower(),
        "payment_status": b.payment_status.value.lower(),
        "total": float(b.total_amount),
        "total_amount": str(b.total_amount),
        "amount_paid": float(b.amount_paid),
    } for b in bills]


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


@router.get("/payments")
def list_payments(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    payments = db.query(VendorPayment).all()
    return [{
        "id": p.id,
        "number": p.payment_number,
        "payment_number": p.payment_number,
        "contact_id": p.contact_id,
        "purchase_bill_id": p.purchase_bill_id,
        "payment_date": p.payment_date.isoformat(),
        "payment_type": "payment",
        "method": "bank",
        "amount": float(p.amount),
        "status": p.status.value.lower(),
    } for p in payments]


@router.post("/payments", status_code=201)
def create_payment(payload: VendorPaymentCreate, db: Session = Depends(get_db),
                    user: User = Depends(require_accountant_or_admin)):
    payment = svc.record_vendor_payment(db, payload, user.id)
    return {"id": payment.id, "payment_number": payment.payment_number, "amount": str(payment.amount)}
