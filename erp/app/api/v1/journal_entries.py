from datetime import date as date_type
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_accountant_or_admin
from app.models.user import User
from app.schemas.master_data import JournalEntryCreate
from app.services.accounting_service import post_journal_entry

from app.models.accounting import JournalEntry

router = APIRouter(prefix="/api/v1/journal-entries", tags=["accounting"])


@router.get("")
def list_journal_entries(
    db: Session = Depends(get_db),
    _: User = Depends(require_accountant_or_admin),
):
    entries = db.query(JournalEntry).all()
    return [
        {
            "id": e.id,
            "entry_number": e.entry_number,
            "reference": e.entry_number,
            "journal_id": e.journal_id,
            "entry_date": e.entry_date.isoformat(),
            "memo": e.narration,
            "status": e.status.value,
        }
        for e in entries
    ]


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
