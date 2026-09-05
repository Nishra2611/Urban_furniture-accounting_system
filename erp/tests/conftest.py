import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.session import Base, get_db
import app.models  # noqa: register all models on Base.metadata
from app.models.master_data import ChartOfAccount
from app.models.accounting import Journal
from app.models.enums import AccountType
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    # Seed the minimal reference data every test needs.
    session.add_all([
        ChartOfAccount(code="1000", name="Cash and Bank", account_type=AccountType.ASSET),
        ChartOfAccount(code="1200", name="Accounts Receivable", account_type=AccountType.ASSET),
        ChartOfAccount(code="2000", name="Accounts Payable", account_type=AccountType.LIABILITY),
        ChartOfAccount(code="4000", name="Sales Revenue", account_type=AccountType.INCOME),
        ChartOfAccount(code="5000", name="Cost of Goods Sold", account_type=AccountType.EXPENSE),
        Journal(code="SALES", name="Sales Journal", journal_type="Sales"),
        Journal(code="PURCHASE", name="Purchase Journal", journal_type="Purchase"),
        Journal(code="RECEIPTS", name="Customer Receipts", journal_type="Cash"),
        Journal(code="PAYMENTS", name="Vendor Payments", journal_type="Bank"),
    ])
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth_headers(client, login_id, password):
    resp = client.post("/api/v1/auth/login", json={"login_id": login_id, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_admin(client, db_session):
    from app.models.user import User
    from app.core.security import hash_password
    from app.models.enums import UserRole

    admin = User(
        name="Admin", login_id="admin01", email="admin@test.local",
        hashed_password=hash_password("Admin@12345"), role=UserRole.ADMINISTRATOR, is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    return auth_headers(client, "admin01", "Admin@12345")
