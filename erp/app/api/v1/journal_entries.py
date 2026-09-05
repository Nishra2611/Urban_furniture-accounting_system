from datetime import date as date_type
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.schemas.master_data import JournalEntryCreate
from app.services.accounting_service import post_journal_entry

router = APIRouter(prefix="/api/v1/journal-entries", tags=["accounting"])


@router.post("", status_code=201)
def create_journal_entry(
    payload: JournalEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_accountant_or_admin),
):
    entry = post_journal_entry(
        db,
        journal_id=payload.journal_id,
        entry_date=date_type.fromisoformat(payload.entry_date),
        lines=[l.model_dump() for l in payload.lines],
        narration=payload.narration,
        analytic_account_id=payload.analytic_account_id,
    )
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "entry_number": entry.entry_number,
        "status": entry.status.value,
    }
