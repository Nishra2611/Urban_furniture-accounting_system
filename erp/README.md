# Urban Furniture Accounting System — Backend

A real, working accounting/ERP backend built with **FastAPI + SQLAlchemy + Alembic + PostgreSQL**,
implementing the complete 51-point functional specification: authentication with RBAC,
master data (contacts, products, chart of accounts, journals, analytics/budgets), sales
(orders → invoices → receipts), purchases (orders → bills → payments), double-entry
accounting, financial reports, a restricted customer portal, and audit logging.

This has been built and verified end-to-end in this environment: migrations were
generated and applied against a real local PostgreSQL 16 instance, the seed script ran
successfully, and the full pytest suite (16 tests covering auth, RBAC, the sales
lifecycle, accounting balance invariants, idempotency, and data isolation) passes.

## 1. Requirements

- Python 3.11+
- PostgreSQL 14+ running locally
- (Optional) Docker, if you'd rather run Postgres in a container

## 2. Quick start (local Postgres)

```bash
# 1. Create the database and user (adjust as you like)
sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'erp_password';"
sudo -u postgres psql -c "CREATE DATABASE erp_db OWNER erp_user;"

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# edit .env if your DB credentials differ

# 4. Run migrations
alembic upgrade head

# 5. Seed default chart of accounts, journals, and an admin user
python -m scripts.seed
# -> login_id: admin01 / password: Admin@12345  (CHANGE THIS IMMEDIATELY)

# 6. Run the API
uvicorn app.main:app --reload
# API now live at http://127.0.0.1:8000, interactive docs at /docs
```

## 2b. Or with Docker (Postgres only; the API itself still runs locally)

```bash
docker compose up -d
# then continue from step 2 above, pointing DATABASE_URL in .env at localhost:5432
```

## 3. Running tests

```bash
pip install -r requirements.txt
pytest -q
```

Tests run against an isolated in-memory SQLite database (via dependency override), so
they do not touch your real Postgres data.

## 4. Architecture

```
app/
  core/        settings, JWT + password hashing, RBAC dependencies
  db/          SQLAlchemy engine/session/Base
  models/      one file per domain: user, master_data, accounting, sales, purchase, audit
  schemas/     Pydantic request/response models
  services/    all business logic — the only layer that touches the DB and enforces rules
  api/v1/      thin FastAPI routers; no business logic lives here
alembic/       migration environment + generated versions
scripts/seed.py  default chart of accounts, journals, and an admin user
tests/         pytest suite (auth, sales lifecycle, portal isolation)
```

### Data flow (per the 51-point spec)
`Auth/Roles → Master Data (Contact, Product, Chart of Accounts, Journals, Analytics) →
Transactions (Sales Order → Sale Invoice → Receipt, Purchase Order → Purchase Bill →
Payment) → Accounting (double-entry Journal Entries) → Reports (Balance Sheet, P&L,
Budget Report)`, plus a separate restricted **User portal** (own invoices/bills only,
pay dues).

## 5. Roles

- **User** — portal only: own invoices/bills, payment status, pay dues.
- **Accountant** — master data, transactions, journal entries, and reports.
- **Administrator** — everything.

Every privileged endpoint checks the role from the authenticated JWT on the backend —
never trusts a client-supplied role. Signup (self-registration) never accepts a role at
all; only `/api/v1/auth/create-user` (Administrator only) can grant User, Accountant,
or Administrator roles.

## 6. Business rules implemented

- Login ID unique, 6–12 chars; email unique (case-insensitive); password >8 chars with
  upper/lower/special character; password confirmation must match.
- Recent-password reuse prevention (last 5 hashes checked).
- Account lockout after `MAX_FAILED_LOGIN_ATTEMPTS` (default 5) for `LOCKOUT_MINUTES`
  (default 15).
- JWTs carry a `jti`; logout inserts it into a revocation table, so logout is a real
  server-side invalidation, not just "forget the client-side token."
- Password-reset tokens are single-use, hashed at rest, and time-limited; the endpoint
  behaves identically whether or not the email exists (no account enumeration).
- Master data is archived (`is_active=False`), never hard-deleted, once it could be
  referenced by a transaction; inactive contacts/products/accounts are rejected for new
  transactions but remain valid for historical records already pointing at them.
- All line items are quantity>0, price>=0, tax>=0 (DB check constraints + service-layer
  validation); every document needs at least one line.
- Sales/Purchase Order → Invoice/Bill conversion is one-to-one (DB unique constraint) —
  an order cannot be invoiced/billed twice.
- Confirming an invoice/bill posts a real, balanced double-entry journal entry
  (`debit == credit`, enforced both in code and via a DB check constraint that a line is
  never debit-and-credit at once). Posting is idempotent per source document (a unique
  constraint on `(source_type, source_id, journal_id)` blocks double-posting).
- Receipts/Payments: contact is always taken from the invoice/bill (never client-
  supplied), amount can't exceed the outstanding balance (no overpayment), and an
  `idempotency_key` makes duplicate submissions return the original result instead of
  creating a second payment. `SELECT ... FOR UPDATE` row locking guards the
  read-modify-write on the invoice/bill during payment.
- Document Status (`Draft/Confirmed/Posted/Cancelled`) and Payment Status
  (`Unpaid/Partially Paid/Paid`) are separate fields, never conflated.
- The User-role portal filters every query by the authenticated user's linked
  `contact_id` at the query level — not just hidden in a UI — so guessing another
  customer's invoice ID returns 404, not someone else's data.
- Every significant action (signup, login, create-user, confirm, payment) writes an
  `AuditLog` row.
- Dashboard counts (`All/Confirmed/Draft` for Sales and Purchase) are computed live from
  the transaction tables, never hardcoded.

## 7. What's intentionally left open

Per the spec (§51), the exact field-by-field layout of every Master Data/transaction
form, the Forgot Password page's exact fields, partial-payment UX beyond the
Paid/Unpaid/Partially Paid states already modeled, exact tax-jurisdiction rules, and
stock/inventory valuation methods were not shown in the source material and are not
invented here. The schema (`Product.track_stock`, `stock_quantity`) leaves room for a
full inventory module without requiring one now.

## 8. Security notes for production

- Change `SECRET_KEY` in `.env` to a long random value before deploying.
- Change the seeded admin password immediately (`admin01` / `Admin@12345`) — it exists
  only so you have a way to log in on a fresh database.
- Put this behind HTTPS; JWTs are bearer tokens.
- The revoked-token table grows forever as-is; in production, prune rows past their
  `expires_at` on a schedule.
