"""Seed reference data: default chart of accounts, journals, and an initial Administrator.

Run with: python -m scripts.seed
Safe to re-run - skips anything that already exists.
"""
from datetime import datetime, timezone

from app.db.session import SessionLocal, engine, Base
from app.models.master_data import ChartOfAccount
from app.models.accounting import Journal
from app.models.user import User, PasswordHistory
from app.models.enums import AccountType, UserRole
from app.core.security import hash_password

DEFAULT_ACCOUNTS = [
    ("1000", "Cash and Bank", AccountType.ASSET),
    ("1200", "Accounts Receivable", AccountType.ASSET),
    ("2000", "Accounts Payable", AccountType.LIABILITY),
    ("3000", "Owner's Equity", AccountType.EQUITY),
    ("4000", "Sales Revenue", AccountType.INCOME),
    ("5000", "Cost of Goods Sold", AccountType.EXPENSE),
]

DEFAULT_JOURNALS = [
    ("SALES", "Sales Journal", "Sales"),
    ("PURCHASE", "Purchase Journal", "Purchase"),
    ("RECEIPTS", "Customer Receipts", "Cash"),
    ("PAYMENTS", "Vendor Payments", "Bank"),
    ("MISC", "Miscellaneous Journal", "Miscellaneous"),
]


def seed():
    Base.metadata.create_all(bind=engine)  # no-op if Alembic already ran; safe either way
    db = SessionLocal()
    try:
        for code, name, acc_type in DEFAULT_ACCOUNTS:
            if not db.query(ChartOfAccount).filter(ChartOfAccount.code == code).first():
                db.add(ChartOfAccount(code=code, name=name, account_type=acc_type))

        for code, name, jtype in DEFAULT_JOURNALS:
            if not db.query(Journal).filter(Journal.code == code).first():
                db.add(Journal(code=code, name=name, journal_type=jtype))

        db.flush()

        if not db.query(User).filter(User.login_id == "admin01").first():
            admin = User(
                name="System Administrator",
                login_id="admin01",
                # email="admin@urbanfurniture.local",
                email="admin@urbanfurniture.com",
                hashed_password=hash_password("Admin@12345"),
                role=UserRole.ADMINISTRATOR,
                is_active=True,
            )
            db.add(admin)
            db.flush()
            db.add(PasswordHistory(
                user_id=admin.id, hashed_password=admin.hashed_password,
                created_at=datetime.now(timezone.utc),
            ))
            print("Created default admin -> login_id: admin01 / password: Admin@12345 (CHANGE THIS)")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
