"""Seed a realistic Urban Furniture demo database.

Safe to rerun: records are looked up by stable codes or document numbers.
Run from the erp directory with: python -m scripts.seed
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.accounting import Journal, JournalEntry, JournalEntryLine
from app.models.audit import AuditLog
from app.models.enums import AccountType, DocumentStatus, PartyType, PaymentStatus, UserRole
from app.models.master_data import AnalyticAccount, AnalyticBudget, ChartOfAccount, Contact, Product, Tax
from app.models.purchase import PurchaseBill, PurchaseBillLine, PurchaseOrder, PurchaseOrderLine, VendorPayment
from app.models.sales import Receipt, SaleInvoice, SaleInvoiceLine, SalesOrder, SalesOrderLine
from app.models.user import PasswordHistory, User
from app.services.numbering_service import DocumentCounter


def one(db, model, **filters):
    return db.query(model).filter_by(**filters).first()


def account(db, code, name, account_type):
    value = one(db, ChartOfAccount, code=code)
    if not value:
        value = ChartOfAccount(code=code, name=name, account_type=account_type)
        db.add(value)
        db.flush()
    return value


def journal(db, code, name, journal_type, debit=None, credit=None):
    value = one(db, Journal, code=code)
    if not value:
        value = Journal(code=code, name=name, journal_type=journal_type)
        db.add(value)
        db.flush()
    if debit:
        value.default_debit_account_id = debit.id
    if credit:
        value.default_credit_account_id = credit.id
    return value


def user(db, login_id, name, email, password, role, contact=None):
    value = one(db, User, login_id=login_id)
    if not value:
        value = User(login_id=login_id, name=name, email=email,
                     hashed_password=hash_password(password), role=role)
        db.add(value)
        db.flush()
        db.add(PasswordHistory(user_id=value.id, hashed_password=value.hashed_password,
                               created_at=datetime.now(timezone.utc)))
    value.name = name
    value.email = email
    value.role = role
    value.is_active = True
    if contact:
        value.contact_id = contact.id
    return value


def contact(db, code, name, party_type, email, phone, receivable=None, payable=None):
    value = one(db, Contact, code=code)
    if not value:
        value = Contact(code=code, name=name, party_type=party_type,
                        email=email, phone=phone)
        db.add(value)
        db.flush()
    value.name = name
    value.party_type = party_type
    value.email = email
    value.phone = phone
    if receivable:
        value.receivable_account_id = receivable.id
    if payable:
        value.payable_account_id = payable.id
    return value


def product(db, code, name, sales_price, purchase_price, tax_rate, stock, income, expense, description):
    value = one(db, Product, code=code)
    if not value:
        value = Product(code=code, name=name, sales_price=sales_price,
                        purchase_price=purchase_price, tax_rate=tax_rate,
                        track_stock=True, stock_quantity=stock,
                        income_account_id=income.id, expense_account_id=expense.id,
                        description=description)
        db.add(value)
    return value


def line_total(quantity, price, tax_rate):
    return (Decimal(quantity) * Decimal(price) *
            (Decimal("1") + Decimal(tax_rate) / Decimal("100"))).quantize(Decimal("0.01"))


def make_sales_order(db, number, contact_id, created_by, order_date, status, lines):
    value = one(db, SalesOrder, order_number=number)
    if value:
        return value
    total = sum((line_total(qty, price, tax) for _, qty, price, tax in lines), Decimal("0"))
    value = SalesOrder(order_number=number, contact_id=contact_id, created_by_id=created_by,
                       order_date=order_date, status=status, total_amount=total)
    value.lines = [SalesOrderLine(product_id=product_id, quantity=qty, unit_price=price,
                                  tax_rate=tax, line_total=line_total(qty, price, tax))
                   for product_id, qty, price, tax in lines]
    db.add(value)
    db.flush()
    return value


def make_invoice(db, number, contact_id, created_by, invoice_date, status, payment_status,
                 amount_paid, sales_order, lines):
    value = one(db, SaleInvoice, invoice_number=number)
    if value:
        return value
    total = sum((line_total(qty, price, tax) for _, qty, price, tax in lines), Decimal("0"))
    value = SaleInvoice(invoice_number=number, contact_id=contact_id, created_by_id=created_by,
                        sales_order_id=sales_order.id if sales_order else None,
                        invoice_date=invoice_date, status=status, payment_status=payment_status,
                        total_amount=total, amount_paid=amount_paid)
    value.lines = [SaleInvoiceLine(product_id=product_id, quantity=qty, unit_price=price,
                                   tax_rate=tax, line_total=line_total(qty, price, tax))
                   for product_id, qty, price, tax in lines]
    db.add(value)
    db.flush()
    return value


def make_purchase_order(db, number, contact_id, created_by, order_date, status, lines):
    value = one(db, PurchaseOrder, order_number=number)
    if value:
        return value
    total = sum((line_total(qty, price, tax) for _, qty, price, tax in lines), Decimal("0"))
    value = PurchaseOrder(order_number=number, contact_id=contact_id, created_by_id=created_by,
                          order_date=order_date, status=status, total_amount=total)
    value.lines = [PurchaseOrderLine(product_id=product_id, quantity=qty, unit_price=price,
                                     tax_rate=tax, line_total=line_total(qty, price, tax))
                   for product_id, qty, price, tax in lines]
    db.add(value)
    db.flush()
    return value


def make_bill(db, number, contact_id, created_by, bill_date, status, payment_status,
              amount_paid, purchase_order, lines):
    value = one(db, PurchaseBill, bill_number=number)
    if value:
        return value
    total = sum((line_total(qty, price, tax) for _, qty, price, tax in lines), Decimal("0"))
    value = PurchaseBill(bill_number=number, contact_id=contact_id, created_by_id=created_by,
                         purchase_order_id=purchase_order.id if purchase_order else None,
                         bill_date=bill_date, status=status, payment_status=payment_status,
                         total_amount=total, amount_paid=amount_paid)
    value.lines = [PurchaseBillLine(product_id=product_id, quantity=qty, unit_price=price,
                                    tax_rate=tax, line_total=line_total(qty, price, tax))
                   for product_id, qty, price, tax in lines]
    db.add(value)
    db.flush()
    return value


def journal_entry(db, number, journal_id, entry_date, narration, lines, analytic_id=None,
                  source_type=None, source_id=None):
    if one(db, JournalEntry, entry_number=number):
        return
    entry = JournalEntry(entry_number=number, journal_id=journal_id, entry_date=entry_date,
                         narration=narration, status=DocumentStatus.POSTED,
                         analytic_account_id=analytic_id, source_type=source_type, source_id=source_id)
    entry.lines = [JournalEntryLine(account_id=account_id, debit=debit, credit=credit,
                                    description=description)
                   for account_id, debit, credit, description in lines]
    db.add(entry)
    db.flush()


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cash = account(db, "1000", "Cash", AccountType.ASSET)
        bank = account(db, "1010", "Bank Account", AccountType.ASSET)
        receivable = account(db, "1100", "Accounts Receivable", AccountType.ASSET)
        inventory = account(db, "1200", "Inventory", AccountType.ASSET)
        payable = account(db, "2000", "Accounts Payable", AccountType.LIABILITY)
        tax_payable = account(db, "2100", "GST/Tax Payable", AccountType.LIABILITY)
        capital = account(db, "3000", "Owner's Capital", AccountType.EQUITY)
        sales_income = account(db, "4000", "Furniture Sales Income", AccountType.INCOME)
        service_income = account(db, "4100", "Service Income", AccountType.INCOME)
        purchase_expense = account(db, "5000", "Furniture Purchase Expense", AccountType.EXPENSE)
        operating_expense = account(db, "5100", "Operating Expenses", AccountType.EXPENSE)
        delivery_expense = account(db, "5200", "Delivery Expense", AccountType.EXPENSE)

        sales_journal = journal(db, "SALES", "Sales Journal", "Sales", receivable, sales_income)
        purchase_journal = journal(db, "PURCH", "Purchase Journal", "Purchase", purchase_expense, payable)
        cash_journal = journal(db, "CASH", "Cash Journal", "Cash", cash, receivable)
        bank_journal = journal(db, "BANK", "Bank Journal", "Bank", bank, receivable)
        receipts_journal = journal(db, "RECEIPTS", "Customer Receipts", "Cash", cash, receivable)
        payments_journal = journal(db, "PAYMENTS", "Vendor Payments", "Bank", payable, bank)
        misc_journal = journal(db, "MISC", "Miscellaneous Journal", "Miscellaneous")

        admin = user(db, "admin01", "Urban Furniture Admin", "admin@urbanfurniture.com",
                     "Admin@12345", UserRole.ADMINISTRATOR)
        accountant = user(db, "accountant01", "Priya Shah", "accountant@urbanfurniture.com",
                         "Accountant@12345", UserRole.ACCOUNTANT)

        rahul = contact(db, "CUST001", "Rahul Mehta", PartyType.CUSTOMER,
                        "rahul@urbanfurniture.com", "9876500011", receivable=receivable)
        aditi = contact(db, "CUST002", "Aditi Patel", PartyType.CUSTOMER,
                        "aditi@example.com", "9876500012", receivable=receivable)
        royal = contact(db, "CUST003", "Royal Interiors", PartyType.CUSTOMER,
                        "accounts@royalinteriors.com", "9876500013", receivable=receivable)
        gujarat = contact(db, "VEND001", "Gujarat Wood Suppliers", PartyType.VENDOR,
                          "sales@gws.com", "9876500021", payable=payable)
        foam = contact(db, "VEND002", "Premium Foam & Fabric", PartyType.VENDOR,
                       "orders@pff.com", "9876500022", payable=payable)
        homestyle = contact(db, "CUSTV001", "HomeStyle Furnishings", PartyType.BOTH,
                            "finance@homestyle.com", "9876500030", receivable, payable)
        user(db, "rahul01", "Rahul Mehta", "rahul@urbanfurniture.com",
             "Rahul@12345", UserRole.USER, rahul)

        products = {}
        for data in [
            ("CHR001", "Executive Office Chair", 8500, 5500, 18, 35, "Ergonomic executive chair with adjustable height"),
            ("TBL001", "Solid Wood Office Table", 18000, 12000, 18, 18, "Solid wood office table with cable management"),
            ("SOF001", "3-Seater Fabric Sofa", 32000, 22000, 18, 12, "Comfortable three-seater fabric sofa"),
            ("BED001", "King Size Wooden Bed", 45000, 31000, 18, 8, "Solid wood king size bed frame"),
            ("CAB001", "Wooden Storage Cabinet", 14500, 9500, 12, 20, "Lockable wooden storage cabinet"),
            ("DES001", "Study Desk", 11000, 7000, 12, 25, "Compact study desk for home and office"),
        ]:
            products[data[0]] = product(db, *data[:1], *data[1:2], *data[2:6], sales_income, purchase_expense, data[6])

        for name, rate in [("GST 0%", 0), ("GST 5%", 5), ("GST 12%", 12), ("GST 18%", 18), ("GST 28%", 28)]:
            if not one(db, Tax, name=name):
                db.add(Tax(name=name, rate=rate, tax_type="GST"))

        analytics = {}
        for code, name in [("SALES", "Sales Department"), ("MFG", "Furniture Manufacturing"),
                           ("SHOWROOM", "Main Showroom"), ("MARKETING", "Marketing"),
                           ("OPERATIONS", "Operations")]:
            analytics[code] = one(db, AnalyticAccount, code=code)
            if not analytics[code]:
                analytics[code] = AnalyticAccount(code=code, name=name)
                db.add(analytics[code])
                db.flush()

        for name, analytic_code, amount in [
            ("Marketing Budget 2026", "MARKETING", 500000),
            ("Showroom Operations 2026", "SHOWROOM", 800000),
            ("Manufacturing Budget 2026", "MFG", 1500000),
            ("Sales Department 2026", "SALES", 750000),
        ]:
            if not one(db, AnalyticBudget, name=name):
                db.add(AnalyticBudget(name=name, analytic_account_id=analytics[analytic_code].id,
                                      period_start="2026-01-01", period_end="2026-12-31", budget_amount=amount))

        sales_lines_1 = [(products["CHR001"].id, 2, 8500, 18), (products["TBL001"].id, 1, 18000, 18)]
        sales_lines_2 = [(products["SOF001"].id, 3, 32000, 18), (products["CAB001"].id, 4, 14500, 12)]
        sales_lines_3 = [(products["BED001"].id, 1, 45000, 18)]
        sales_lines_4 = [(products["DES001"].id, 1, 11000, 12)]
        so1 = make_sales_order(db, "SO-2026-0001", rahul.id, accountant.id, date(2026, 9, 1), DocumentStatus.CONFIRMED, sales_lines_1)
        so2 = make_sales_order(db, "SO-2026-0002", royal.id, accountant.id, date(2026, 9, 2), DocumentStatus.CONFIRMED, sales_lines_2)
        so3 = make_sales_order(db, "SO-2026-0003", aditi.id, accountant.id, date(2026, 9, 4), DocumentStatus.DRAFT, sales_lines_3)
        make_sales_order(db, "SO-2026-0004", homestyle.id, accountant.id, date(2026, 9, 5), DocumentStatus.CANCELLED, sales_lines_4)

        inv1 = make_invoice(db, "INV-2026-0001", rahul.id, accountant.id, date(2026, 9, 2), DocumentStatus.POSTED, PaymentStatus.PARTIALLY_PAID, 20000, so1, sales_lines_1)
        inv2 = make_invoice(db, "INV-2026-0002", royal.id, accountant.id, date(2026, 9, 3), DocumentStatus.POSTED, PaymentStatus.PAID, Decimal("178240"), so2, sales_lines_2)
        make_invoice(db, "INV-2026-0003", aditi.id, accountant.id, date(2026, 9, 5), DocumentStatus.DRAFT, PaymentStatus.UNPAID, 0, None, sales_lines_3)

        purchase_lines_1 = [(products["TBL001"].id, 10, 12000, 18), (products["DES001"].id, 10, 7000, 12)]
        purchase_lines_2 = [(products["SOF001"].id, 5, 22000, 18)]
        purchase_lines_3 = [(products["CAB001"].id, 4, 9500, 12)]
        po1 = make_purchase_order(db, "PO-2026-0001", gujarat.id, accountant.id, date(2026, 9, 1), DocumentStatus.CONFIRMED, purchase_lines_1)
        po2 = make_purchase_order(db, "PO-2026-0002", foam.id, accountant.id, date(2026, 9, 2), DocumentStatus.CONFIRMED, purchase_lines_2)
        make_purchase_order(db, "PO-2026-0003", gujarat.id, accountant.id, date(2026, 9, 5), DocumentStatus.DRAFT, purchase_lines_3)
        bill1 = make_bill(db, "BILL-2026-0001", gujarat.id, accountant.id, date(2026, 9, 3), DocumentStatus.POSTED, PaymentStatus.PARTIALLY_PAID, 100000, po1, purchase_lines_1)
        bill2 = make_bill(db, "BILL-2026-0002", foam.id, accountant.id, date(2026, 9, 4), DocumentStatus.POSTED, PaymentStatus.UNPAID, 0, po2, purchase_lines_2)
        make_bill(db, "BILL-2026-0003", gujarat.id, accountant.id, date(2026, 9, 5), DocumentStatus.DRAFT, PaymentStatus.UNPAID, 0, None, purchase_lines_3)

        if not one(db, Receipt, receipt_number="REC-2026-0001"):
            db.add(Receipt(receipt_number="REC-2026-0001", sale_invoice_id=inv1.id, contact_id=rahul.id, amount=20000,
                           receipt_date=date(2026, 9, 4), status=DocumentStatus.POSTED,
                           idempotency_key="seed-rec-1", created_by_id=accountant.id))
        if not one(db, Receipt, receipt_number="REC-2026-0002"):
            db.add(Receipt(receipt_number="REC-2026-0002", sale_invoice_id=inv2.id, contact_id=royal.id, amount=178240,
                           receipt_date=date(2026, 9, 5), status=DocumentStatus.POSTED,
                           idempotency_key="seed-rec-2", created_by_id=accountant.id))
        if not one(db, VendorPayment, payment_number="VPAY-2026-0001"):
            db.add(VendorPayment(payment_number="VPAY-2026-0001", purchase_bill_id=bill1.id, contact_id=gujarat.id,
                                 amount=100000, payment_date=date(2026, 9, 5), status=DocumentStatus.POSTED,
                                 idempotency_key="seed-pay-1", created_by_id=accountant.id))
        db.flush()

        receipt1 = one(db, Receipt, receipt_number="REC-2026-0001")
        receipt2 = one(db, Receipt, receipt_number="REC-2026-0002")
        vendor_payment = one(db, VendorPayment, payment_number="VPAY-2026-0001")
        journal_entry(db, "JE-2026-0001", sales_journal.id, date(2026, 9, 2), "Invoice INV-2026-0001",
                      [(receivable.id, 41300, 0, "Accounts receivable"), (sales_income.id, 0, 35000, "Furniture sales"), (tax_payable.id, 0, 6300, "GST payable")], analytics["SALES"].id, "SaleInvoice", inv1.id)
        journal_entry(db, "JE-2026-0002", sales_journal.id, date(2026, 9, 3), "Invoice INV-2026-0002",
                      [(receivable.id, 178240, 0, "Accounts receivable"), (sales_income.id, 0, 167000, "Furniture sales"), (tax_payable.id, 0, 11240, "GST payable")], analytics["SALES"].id, "SaleInvoice", inv2.id)
        journal_entry(db, "JE-2026-0003", receipts_journal.id, date(2026, 9, 4), "Receipt REC-2026-0001",
                      [(cash.id, 20000, 0, "Cash received"), (receivable.id, 0, 20000, "Receivable settled")], source_type="Receipt", source_id=receipt1.id)
        journal_entry(db, "JE-2026-0004", receipts_journal.id, date(2026, 9, 5), "Receipt REC-2026-0002",
                      [(cash.id, 178240, 0, "Cash received"), (receivable.id, 0, 178240, "Receivable settled")], source_type="Receipt", source_id=receipt2.id)
        journal_entry(db, "JE-2026-0005", purchase_journal.id, date(2026, 9, 3), "Bill BILL-2026-0001",
                      [(purchase_expense.id, 190000, 0, "Furniture purchases"), (tax_payable.id, 30000, 0, "GST input"), (payable.id, 0, 220000, "Accounts payable")], analytics["MFG"].id, "PurchaseBill", bill1.id)
        journal_entry(db, "JE-2026-0006", payments_journal.id, date(2026, 9, 5), "Payment VPAY-2026-0001",
                      [(payable.id, 100000, 0, "Payable settled"), (bank.id, 0, 100000, "Bank payment")], source_type="VendorPayment", source_id=vendor_payment.id)

        for prefix, value in [("SO", 4), ("PO", 3), ("INV", 3), ("BILL", 3), ("REC", 2), ("PAY", 1), ("JE", 6)]:
            counter = one(db, DocumentCounter, prefix=prefix)
            if not counter:
                db.add(DocumentCounter(prefix=prefix, last_value=value))
            elif counter.last_value < value:
                counter.last_value = value

        if not db.query(AuditLog).filter(AuditLog.details == "Demo dataset seeded").first():
            db.add(AuditLog(user_id=admin.id, action="SEED", entity_type="System",
                            details="Demo dataset seeded", created_at=datetime.now(timezone.utc)))

        db.commit()
        print("Base seed complete.")

        # Seed 300+ realistic extended demo entries
        from scripts.seed_demo_300 import seed_demo_300
        seed_demo_300()

        print("Admin: admin01 / Admin@12345")
        print("Accountant: accountant01 / Accountant@12345")
        print("Contact User: rahul01 / Rahul@12345")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

