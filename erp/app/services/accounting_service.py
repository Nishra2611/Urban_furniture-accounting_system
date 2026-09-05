from datetime import date as date_type, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.accounting import Journal, JournalEntry, JournalEntryLine
from app.models.enums import DocumentStatus
from app.services.numbering_service import next_number
from app.services.master_data_service import get_active_or_404
from app.models.master_data import ChartOfAccount


def post_journal_entry(
    db: Session,
    journal_id: int,
    entry_date: date_type,
    lines: list[dict],
    narration: str | None = None,
    analytic_account_id: int | None = None,
    source_type: str | None = None,
    source_id: int | None = None,
) -> JournalEntry:
    """Creates and posts a balanced double-entry journal entry.

    `lines` is a list of {"account_id", "debit", "credit", "description"} dicts.
    Prevents duplicate posting for the same source document via the
    (source_type, source_id, journal_id) unique constraint.
    """
    if not lines or len(lines) < 1:
        raise HTTPException(status_code=422, detail="A journal entry needs at least one line")

    if source_type and source_id:
        existing = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.source_type == source_type,
                JournalEntry.source_id == source_id,
                JournalEntry.journal_id == journal_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="This transaction has already been posted")

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line in lines:
        debit = Decimal(line.get("debit", 0) or 0)
        credit = Decimal(line.get("credit", 0) or 0)
        if debit > 0 and credit > 0:
            raise HTTPException(status_code=422, detail="A line cannot have both a debit and a credit")
        if debit == 0 and credit == 0:
            raise HTTPException(status_code=422, detail="A line must have either a debit or a credit")
        get_active_or_404(db, ChartOfAccount, line["account_id"])
        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        raise HTTPException(
            status_code=422,
            detail=f"Journal entry is not balanced: debit {total_debit} != credit {total_credit}",
        )

    journal = get_active_or_404(db, Journal, journal_id)
    entry = JournalEntry(
        entry_number=next_number(db, f"JE-{journal.code}"),
        journal_id=journal_id,
        entry_date=entry_date,
        narration=narration,
        analytic_account_id=analytic_account_id,
        status=DocumentStatus.POSTED,
        source_type=source_type,
        source_id=source_id,
    )
    for line in lines:
        entry.lines.append(
            JournalEntryLine(
                account_id=line["account_id"],
                debit=Decimal(line.get("debit", 0) or 0),
                credit=Decimal(line.get("credit", 0) or 0),
                description=line.get("description"),
            )
        )
    db.add(entry)
    db.flush()
    return entry
