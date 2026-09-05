from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.services import report_service as svc

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/balance-sheet")
def balance_sheet(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return svc.balance_sheet(db)


@router.get("/profit-and-loss")
def profit_and_loss(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return svc.profit_and_loss(db)


@router.get("/budget-report")
def budget_report(db: Session = Depends(get_db), _: User = Depends(require_accountant_or_admin)):
    return svc.budget_report(db)
