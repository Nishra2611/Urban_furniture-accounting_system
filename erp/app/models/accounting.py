from decimal import Decimal
from typing import Optional
from datetime import date as date_type

from sqlalchemy import (
    String, Integer, Numeric, Date, ForeignKey, Text, Boolean,
    Enum as SAEnum, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, ActiveMixin
from app.models.enums import DocumentStatus


class Journal(Base, TimestampMixin, ActiveMixin):
    __tablename__ = "journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # e.g. Sales, Purchase, Cash, Bank, Miscellaneous - kept as free text to avoid over-constraining
    journal_type: Mapped[str] = mapped_column(String(30), nullable=False, default="Miscellaneous")
    default_debit_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )
    default_credit_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("chart_of_accounts.id"), nullable=True
    )


class JournalEntry(Base, TimestampMixin):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_number: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    journal_id: Mapped[int] = mapped_column(ForeignKey("journals.id"), nullable=False)
    entry_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False
    )
    analytic_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("analytic_accounts.id"), nullable=True
    )

    # Origin reference so postings can be traced back to the source transaction
    # and duplicate posting for the same source document can be prevented.
    source_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    lines: Mapped[list["JournalEntryLine"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "journal_id", name="uq_journal_entry_source"),
    )


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("chart_of_accounts.id"), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    entry: Mapped["JournalEntry"] = relationship(back_populates="lines")

    __table_args__ = (
        # A line must be a debit OR a credit, never both, and never neither.
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",
            name="ck_journal_line_single_side",
        ),
    )
