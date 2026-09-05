from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.accounting import JournalEntryLine, JournalEntry
from app.models.master_data import ChartOfAccount
from app.models.enums import AccountType, DocumentStatus


def _account_balances(db: Session, account_types: list[AccountType]) -> list[dict]:
    rows = (
        db.query(
            ChartOfAccount.code,
            ChartOfAccount.name,
            ChartOfAccount.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("credit"),
        )
        .outerjoin(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccount.id)
        .outerjoin(JournalEntry, JournalEntry.id == JournalEntryLine.entry_id)
        .filter(ChartOfAccount.account_type.in_(account_types))
        .filter(
            (JournalEntry.status == DocumentStatus.POSTED) | (JournalEntry.id.is_(None))
        )
        .group_by(ChartOfAccount.id, ChartOfAccount.code, ChartOfAccount.name, ChartOfAccount.account_type)
        .all()
    )
    result = []
    for code, name, account_type, debit, credit in rows:
        # Assets/Expenses are debit-normal; Liabilities/Equity/Income are credit-normal.
        if account_type in (AccountType.ASSET, AccountType.EXPENSE):
            balance = Decimal(debit) - Decimal(credit)
        else:
            balance = Decimal(credit) - Decimal(debit)
        result.append({"code": code, "name": name, "balance": float(balance)})
    return result


def balance_sheet(db: Session) -> dict:
    assets = _account_balances(db, [AccountType.ASSET])
    liabilities = _account_balances(db, [AccountType.LIABILITY])
    equity = _account_balances(db, [AccountType.EQUITY])
    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": sum(a["balance"] for a in assets),
        "total_liabilities": sum(l["balance"] for l in liabilities),
        "total_equity": sum(e["balance"] for e in equity),
    }


def profit_and_loss(db: Session) -> dict:
    income = _account_balances(db, [AccountType.INCOME])
    expense = _account_balances(db, [AccountType.EXPENSE])
    total_income = sum(i["balance"] for i in income)
    total_expense = sum(e["balance"] for e in expense)
    return {
        "income": income,
        "expense": expense,
        "total_income": total_income,
        "total_expense": total_expense,
        "net_profit": total_income - total_expense,
    }


def budget_report(db: Session) -> dict:
    from app.services.dashboard_service import budget_summary
    return budget_summary(db)
