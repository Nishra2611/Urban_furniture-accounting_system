from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sales import SalesOrder
from app.models.purchase import PurchaseOrder
from app.models.master_data import AnalyticBudget
from app.models.accounting import JournalEntryLine, JournalEntry
from app.models.enums import DocumentStatus


def _counts(db: Session, model):
    rows = db.query(model.status, func.count(model.id)).group_by(model.status).all()
    counts = {status.value: 0 for status in DocumentStatus}
    for status, count in rows:
        counts[status.value] = count
    all_count = sum(counts.values())
    return {
        "all": all_count,
        "confirmed": counts.get(DocumentStatus.CONFIRMED.value, 0),
        "draft": counts.get(DocumentStatus.DRAFT.value, 0),
    }


def sales_summary(db: Session) -> dict:
    return _counts(db, SalesOrder)


def purchase_summary(db: Session) -> dict:
    return _counts(db, PurchaseOrder)


def budget_summary(db: Session) -> dict:
    """Achieved = actual posted spend against analytic accounts with a budget.
    Committed = draft/confirmed-but-not-yet-posted transactions tied to those accounts (approximated
    here as posted amount not yet fully settled). Numbers are derived from real records only.
    """
    total_budget = db.query(func.coalesce(func.sum(AnalyticBudget.budget_amount), 0)).scalar() or Decimal("0")

    achieved = (
        db.query(func.coalesce(func.sum(JournalEntryLine.debit + JournalEntryLine.credit), 0))
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(JournalEntry.analytic_account_id.isnot(None))
        .filter(JournalEntry.status == DocumentStatus.POSTED)
        .scalar() or Decimal("0")
    )

    committed = Decimal("0")  # placeholder until draft-commitment tracking is defined by the Data Input spec

    return {
        "achieved": float(achieved),
        "budget": float(total_budget),
        "committed": float(committed),
    }
