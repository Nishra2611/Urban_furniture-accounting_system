from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.services import dashboard_service as svc

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return {
        "sales": svc.sales_summary(db),
        "purchase": svc.purchase_summary(db),
        "budget": svc.budget_summary(db),
    }
