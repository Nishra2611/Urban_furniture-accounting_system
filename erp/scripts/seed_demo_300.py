"""Seeder extension generating 300+ realistic, mathematically balanced, and idempotent ERP database records.

Run from the erp directory with: python -m scripts.seed
"""
from datetime import date, datetime, timedelta, timezone
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


def line_total(quantity, price, tax_rate):
    return (Decimal(quantity) * Decimal(price) *
            (Decimal("1") + Decimal(tax_rate) / Decimal("100"))).quantize(Decimal("0.01"))


def seed_demo_300():
    db = SessionLocal()
    try:
        # 1. Fetch Key Accounts & Core Infrastructure
        cash = one(db, ChartOfAccount, code="1000") or ChartOfAccount(code="1000", name="Cash", account_type=AccountType.ASSET)
        bank = one(db, ChartOfAccount, code="1010") or ChartOfAccount(code="1010", name="Bank Account", account_type=AccountType.ASSET)
        receivable = one(db, ChartOfAccount, code="1100") or ChartOfAccount(code="1100", name="Accounts Receivable", account_type=AccountType.ASSET)
        inventory = one(db, ChartOfAccount, code="1200") or ChartOfAccount(code="1200", name="Inventory", account_type=AccountType.ASSET)
        payable = one(db, ChartOfAccount, code="2000") or ChartOfAccount(code="2000", name="Accounts Payable", account_type=AccountType.LIABILITY)
        tax_payable = one(db, ChartOfAccount, code="2100") or ChartOfAccount(code="2100", name="GST/Tax Payable", account_type=AccountType.LIABILITY)
        sales_income = one(db, ChartOfAccount, code="4000") or ChartOfAccount(code="4000", name="Furniture Sales Income", account_type=AccountType.INCOME)
        purchase_expense = one(db, ChartOfAccount, code="5000") or ChartOfAccount(code="5000", name="Furniture Purchase Expense", account_type=AccountType.EXPENSE)

        sales_journal = one(db, Journal, code="SALES")
        purchase_journal = one(db, Journal, code="PURCH")
        receipts_journal = one(db, Journal, code="RECEIPTS") or sales_journal
        payments_journal = one(db, Journal, code="PAYMENTS") or purchase_journal

        accountant = one(db, User, login_id="accountant01")

        # 2. Contacts (25 Realistic Contacts)
        contacts_data = [
            # Customers (15)
            ("CUST-101", "Apex Corporate Hub Pvt Ltd", PartyType.CUSTOMER, "accounts@apexcorporate.com", "9876510001"),
            ("CUST-102", "Neelam Architects & Designers", PartyType.CUSTOMER, "finance@neelamarch.com", "9876510002"),
            ("CUST-103", "Zenith Tech Park Solutions", PartyType.CUSTOMER, "billing@zenithtech.com", "9876510003"),
            ("CUST-104", "Metro Workspace Systems", PartyType.CUSTOMER, "contact@metrowork.com", "9876510004"),
            ("CUST-105", "Urban Edge Living Spaces", PartyType.CUSTOMER, "support@urbanedge.com", "9876510005"),
            ("CUST-106", "Vanguard Financial Advisors", PartyType.CUSTOMER, "admin@vanguardfin.com", "9876510006"),
            ("CUST-107", "Starlight Cafe & Lounge", PartyType.CUSTOMER, "orders@starlightcafe.com", "9876510007"),
            ("CUST-108", "Silverline Luxury Apartments", PartyType.CUSTOMER, "procurement@silverline.com", "9876510008"),
            ("CUST-109", "Prestige Commercial Plaza", PartyType.CUSTOMER, "info@prestigeplaza.com", "9876510009"),
            ("CUST-110", "Aura Wellness & Dental Clinic", PartyType.CUSTOMER, "reception@aurawellness.com", "9876510010"),
            ("CUST-111", "Horizon Global Tech Systems", PartyType.CUSTOMER, "accounts@horizontch.com", "9876510011"),
            ("CUST-112", "Summit Tower Office Suites", PartyType.CUSTOMER, "management@summittower.com", "9876510012"),
            ("CUST-113", "Pioneer Legal Chambers", PartyType.CUSTOMER, "billing@pioneerlegal.com", "9876510013"),
            ("CUST-114", "Elegance Hotel & Suites", PartyType.CUSTOMER, "purchase@elegancehotel.com", "9876510014"),
            ("CUST-115", "Oasis Coworking Space Hub", PartyType.CUSTOMER, "hello@oasiscowork.com", "9876510015"),
            # Vendors (8)
            ("VEND-101", "Godrej Teak Wood Suppliers", PartyType.VENDOR, "sales@godrejteak.com", "9876520001"),
            ("VEND-102", "ModuForm Hardware & Fittings", PartyType.VENDOR, "orders@moduform.com", "9876520002"),
            ("VEND-103", "Luxe Fabrics & Upholstery Ltd", PartyType.VENDOR, "contact@luxefabrics.com", "9876520003"),
            ("VEND-104", "SteelCraft Furniture Frames", PartyType.VENDOR, "supplies@steelcraft.com", "9876520004"),
            ("VEND-105", "GreenPly Premium Plywood", PartyType.VENDOR, "dealer@greenplytraders.com", "9876520005"),
            ("VEND-106", "PolyFoam Cushioning & Foam", PartyType.VENDOR, "info@polyfoam.com", "9876520006"),
            ("VEND-107", "GlassTech Tempered Tops Co", PartyType.VENDOR, "sales@glasstech.com", "9876520007"),
            ("VEND-108", "FineFinish Wood Polish & Varnish", PartyType.VENDOR, "billing@finefinish.com", "9876520008"),
            # Both (2)
            ("BOTH-101", "FurnishKart Trade Mart", PartyType.BOTH, "trade@furnishkart.com", "9876530001"),
            ("BOTH-102", "Global Office Essentials", PartyType.BOTH, "orders@globaloffice.com", "9876530002"),
        ]

        contacts_map = {}
        for code, name, party_type, email, phone in contacts_data:
            c = one(db, Contact, code=code)
            if not c:
                c = Contact(code=code, name=name, party_type=party_type, email=email, phone=phone,
                            receivable_account_id=receivable.id if party_type in (PartyType.CUSTOMER, PartyType.BOTH) else None,
                            payable_account_id=payable.id if party_type in (PartyType.VENDOR, PartyType.BOTH) else None)
                db.add(c)
                db.flush()
            contacts_map[code] = c

        # 3. Products (30 Realistic Furniture Items)
        products_data = [
            ("PROD-CHR-01", "Executive Mesh Chair Pro", 9500, 6200, 18, 50, "Ergonomic mesh chair with lumbar support"),
            ("PROD-CHR-02", "Leather Boardroom Armchair", 14000, 9200, 18, 30, "Genuine leather swivel armchair"),
            ("PROD-CHR-03", "Ergonomic Visitor Chair", 4500, 2800, 12, 60, "Padded visitor chair with chrome sledge base"),
            ("PROD-CHR-04", "High-Back Gaming & Work Chair", 16500, 11000, 18, 25, "Multi-adjustable high back chair"),
            ("PROD-CHR-05", "Stackable Seminar Chair", 2500, 1500, 12, 100, "Lightweight stackable polypropylene chair"),
            ("PROD-CHR-06", "Bar Stool Chrome Base", 5500, 3400, 18, 40, "Adjustable height swivel bar stool"),
            
            ("PROD-TBL-01", "Teak Boardroom Table 10-Seater", 55000, 36000, 18, 10, "Solid teak conference table with wire box"),
            ("PROD-TBL-02", "Modular L-Shape Executive Desk", 28000, 18500, 18, 20, "L-shaped desk with side return cabinet"),
            ("PROD-TBL-03", "Electric Height Adjustable Desk", 38000, 25000, 18, 15, "Dual motor sit-stand ergonomic desk"),
            ("PROD-TBL-04", "Glass Top Coffee Lounge Table", 9800, 6200, 18, 25, "Tempered glass coffee table with wood base"),
            ("PROD-TBL-05", "Folding Seminar Work Table", 12500, 8000, 12, 35, "Flip-top mobile training table on wheels"),
            ("PROD-TBL-06", "Compact Home Study Desk", 8500, 5200, 12, 45, "Space-saving desk with drawer unit"),

            ("PROD-CAB-01", "Metal Filing Cabinet 4-Drawer", 12800, 8200, 12, 30, "Central locking heavy duty filing cabinet"),
            ("PROD-CAB-02", "Wooden Credenza Sideboard Unit", 22000, 14500, 18, 18, "Executive wooden credenza storage cabinet"),
            ("PROD-CAB-03", "Modular Wall Bookshelf Unit", 18500, 11800, 12, 22, "Open grid display bookshelf system"),
            ("PROD-CAB-04", "Under-Desk Mobile Pedestal", 6500, 4100, 12, 50, "3-drawer lockable pedestal on casters"),
            ("PROD-CAB-05", "Glass Door Display Cupboard", 26000, 17000, 18, 12, "Toughened glass door trophy cupboard"),

            ("PROD-SOF-01", "Chesterfield Leather Sofa 3-Seater", 48000, 32000, 18, 8, "Classic tufted leather lounge sofa"),
            ("PROD-SOF-02", "L-Shape Sectional Fabric Sofa", 39000, 25500, 18, 10, "Modern modular fabric corner sofa"),
            ("PROD-SOF-03", "Recliner Armchair Microfiber", 24000, 15800, 18, 15, "Single seater manual recliner chair"),
            ("PROD-SOF-04", "Velvet Ottoman Bench Pouf", 7500, 4600, 12, 30, "Upholstered velvet accent footstool"),

            ("PROD-BED-01", "Solid Teak King Bed Frame", 52000, 35000, 18, 6, "Premium teak bed with hydraulic storage"),
            ("PROD-BED-02", "Queen Storage Platform Bed", 38000, 24800, 18, 9, "Upholstered headboard queen storage bed"),
            ("PROD-BED-03", "Nightstand Bedside Table Pair", 8200, 5100, 12, 25, "Set of 2 wooden bedside tables"),
            ("PROD-BED-04", "Modular 3-Door Sliding Wardrobe", 46000, 30000, 18, 7, "Full height wardrobe with mirror door"),

            ("PROD-SRV-01", "Office Furniture Layout Design", 15000, 8000, 18, 0, "Professional 3D space planning service"),
            ("PROD-SRV-02", "Furniture Assembly & Installation", 5000, 2500, 18, 0, "On-site expert assembly and fitting"),
            ("PROD-SRV-03", "Wood Re-Polishing & Maintenance", 8000, 4000, 18, 0, "Annual maintenance and polish service"),

            ("PROD-CMB-01", "Executive Suite Package Set", 85000, 56000, 18, 5, "Desk + Mesh Chair + Credenza bundle"),
            ("PROD-CMB-02", "Conference Room 10-Chair Bundle", 115000, 78000, 18, 4, "Boardroom table + 10 leather chairs"),
        ]

        products_map = {}
        for code, name, sales_p, purch_p, tax, stock, desc in products_data:
            p = one(db, Product, code=code)
            if not p:
                p = Product(code=code, name=name, sales_price=Decimal(sales_p),
                            purchase_price=Decimal(purch_p), tax_rate=Decimal(tax),
                            track_stock=(stock > 0), stock_quantity=Decimal(stock),
                            income_account_id=sales_income.id, expense_account_id=purchase_expense.id,
                            description=desc)
                db.add(p)
                db.flush()
            products_map[code] = p

        # 4. Analytic Accounts & Budgets (10 Accounts & Budgets)
        analytics_data = [
            ("ANL-MUM-SR", "Mumbai Showroom"),
            ("ANL-DEL-SR", "Delhi NCR Showroom"),
            ("ANL-BLR-TECH", "Bangalore Tech Park Supply"),
            ("ANL-PUNE-CORP", "Pune Corporate HQ"),
            ("ANL-HYD-MFG", "Hyderabad Manufacturing Unit"),
        ]
        analytics_map = {}
        for code, name in analytics_data:
            anl = one(db, AnalyticAccount, code=code)
            if not anl:
                anl = AnalyticAccount(code=code, name=name)
                db.add(anl)
                db.flush()
            analytics_map[code] = anl

        budgets_data = [
            ("Mumbai Showroom Ops Q3-Q4", "ANL-MUM-SR", 1200000),
            ("Delhi Showroom Expansion 2026", "ANL-DEL-SR", 1800000),
            ("Bangalore Tech Park Sales Q3", "ANL-BLR-TECH", 950000),
            ("Pune Corporate Upgrade 2026", "ANL-PUNE-CORP", 600000),
            ("Hyderabad Plant Automation", "ANL-HYD-MFG", 2500000),
        ]
        for b_name, anl_code, amount in budgets_data:
            if not one(db, AnalyticBudget, name=b_name):
                db.add(AnalyticBudget(name=b_name, analytic_account_id=analytics_map[anl_code].id,
                                      period_start="2026-07-01", period_end="2026-12-31", budget_amount=Decimal(amount)))

        db.flush()

        # Helper sequence data for transaction creation
        customer_codes = [c[0] for c in contacts_data if c[2] in (PartyType.CUSTOMER, PartyType.BOTH)]
        vendor_codes = [c[0] for c in contacts_data if c[2] in (PartyType.VENDOR, PartyType.BOTH)]
        product_codes = [p[0] for p in products_data]

        base_date = date(2026, 7, 1)

        # 5. Sales Orders (50 Entries: SO-2026-0101 to SO-2026-0150)
        sales_orders_map = {}
        for i in range(1, 51):
            so_num = f"SO-2026-0{100 + i}"
            cust_code = customer_codes[(i - 1) % len(customer_codes)]
            cust = contacts_map[cust_code]
            so_date = base_date + timedelta(days=(i * 1.2))
            status = DocumentStatus.CONFIRMED if i % 6 != 0 else (DocumentStatus.DRAFT if i % 2 == 0 else DocumentStatus.CANCELLED)

            p1 = products_map[product_codes[(i * 3) % len(product_codes)]]
            p2 = products_map[product_codes[(i * 3 + 1) % len(product_codes)]]
            lines_spec = [
                (p1.id, (i % 5) + 1, p1.sales_price, p1.tax_rate),
                (p2.id, (i % 3) + 1, p2.sales_price, p2.tax_rate),
            ]
            
            so = one(db, SalesOrder, order_number=so_num)
            if not so:
                tot = sum((line_total(q, pr, tx) for _, q, pr, tx in lines_spec), Decimal("0"))
                so = SalesOrder(order_number=so_num, contact_id=cust.id, created_by_id=accountant.id,
                                order_date=so_date, status=status, total_amount=tot)
                so.lines = [SalesOrderLine(product_id=pid, quantity=Decimal(q), unit_price=Decimal(pr),
                                           tax_rate=Decimal(tx), line_total=line_total(q, pr, tx))
                            for pid, q, pr, tx in lines_spec]
                db.add(so)
                db.flush()
            sales_orders_map[so_num] = so

        # 6. Sale Invoices & Receipts (45 Invoices & 30 Receipts)
        invoices_map = {}
        receipts_count = 0
        for i in range(1, 46):
            inv_num = f"INV-2026-0{100 + i}"
            so_num = f"SO-2026-0{100 + i}"
            so = sales_orders_map.get(so_num)
            cust_code = customer_codes[(i - 1) % len(customer_codes)]
            cust = contacts_map[cust_code]
            inv_date = base_date + timedelta(days=(i * 1.2) + 2)

            status = DocumentStatus.POSTED if i <= 38 else DocumentStatus.DRAFT
            lines_spec = [(l.product_id, l.quantity, l.unit_price, l.tax_rate) for l in so.lines] if so else [
                (products_map["PROD-CHR-01"].id, 2, Decimal(9500), Decimal(18))
            ]
            tot = sum((line_total(q, pr, tx) for _, q, pr, tx in lines_spec), Decimal("0"))

            # Payment status & amount paid logic
            if status == DocumentStatus.DRAFT:
                pay_status = PaymentStatus.UNPAID
                amt_paid = Decimal("0")
            elif i % 3 == 1:
                pay_status = PaymentStatus.PAID
                amt_paid = tot
            elif i % 3 == 2:
                pay_status = PaymentStatus.PARTIALLY_PAID
                amt_paid = (tot * Decimal("0.5")).quantize(Decimal("0.01"))
            else:
                pay_status = PaymentStatus.UNPAID
                amt_paid = Decimal("0")

            inv = one(db, SaleInvoice, invoice_number=inv_num)
            if not inv:
                inv = SaleInvoice(invoice_number=inv_num, contact_id=cust.id, created_by_id=accountant.id,
                                  sales_order_id=so.id if (so and so.status == DocumentStatus.CONFIRMED) else None,
                                  invoice_date=inv_date, status=status, payment_status=pay_status,
                                  total_amount=tot, amount_paid=amt_paid)
                inv.lines = [SaleInvoiceLine(product_id=pid, quantity=Decimal(q), unit_price=Decimal(pr),
                                             tax_rate=Decimal(tx), line_total=line_total(q, pr, tx))
                             for pid, q, pr, tx in lines_spec]
                db.add(inv)
                db.flush()
            invoices_map[inv_num] = inv

            # Generate Receipt if payment was made (up to 30 receipts)
            if amt_paid > 0 and receipts_count < 30:
                receipts_count += 1
                rec_num = f"REC-2026-0{100 + receipts_count}"
                rec = one(db, Receipt, receipt_number=rec_num)
                if not rec:
                    rec = Receipt(receipt_number=rec_num, sale_invoice_id=inv.id, contact_id=cust.id,
                                  amount=amt_paid, receipt_date=inv_date + timedelta(days=3),
                                  status=DocumentStatus.POSTED, idempotency_key=f"seed-rec-300-{receipts_count}",
                                  created_by_id=accountant.id)
                    db.add(rec)
                    db.flush()

        # 7. Purchase Orders (45 Entries: PO-2026-0101 to PO-2026-0145)
        purchase_orders_map = {}
        for i in range(1, 46):
            po_num = f"PO-2026-0{100 + i}"
            vend_code = vendor_codes[(i - 1) % len(vendor_codes)]
            vend = contacts_map[vend_code]
            po_date = base_date + timedelta(days=(i * 1.3))
            status = DocumentStatus.CONFIRMED if i % 5 != 0 else (DocumentStatus.DRAFT if i % 2 == 0 else DocumentStatus.CANCELLED)

            p1 = products_map[product_codes[(i * 2) % len(product_codes)]]
            p2 = products_map[product_codes[(i * 2 + 1) % len(product_codes)]]
            lines_spec = [
                (p1.id, (i % 4) + 5, p1.purchase_price, p1.tax_rate),
                (p2.id, (i % 3) + 2, p2.purchase_price, p2.tax_rate),
            ]

            po = one(db, PurchaseOrder, order_number=po_num)
            if not po:
                tot = sum((line_total(q, pr, tx) for _, q, pr, tx in lines_spec), Decimal("0"))
                po = PurchaseOrder(order_number=po_num, contact_id=vend.id, created_by_id=accountant.id,
                                   order_date=po_date, status=status, total_amount=tot)
                po.lines = [PurchaseOrderLine(product_id=pid, quantity=Decimal(q), unit_price=Decimal(pr),
                                              tax_rate=Decimal(tx), line_total=line_total(q, pr, tx))
                            for pid, q, pr, tx in lines_spec]
                db.add(po)
                db.flush()
            purchase_orders_map[po_num] = po

        # 8. Purchase Bills & Vendor Payments (40 Bills & 25 Payments)
        bills_map = {}
        payments_count = 0
        for i in range(1, 41):
            bill_num = f"BILL-2026-0{100 + i}"
            po_num = f"PO-2026-0{100 + i}"
            po = purchase_orders_map.get(po_num)
            vend_code = vendor_codes[(i - 1) % len(vendor_codes)]
            vend = contacts_map[vend_code]
            bill_date = base_date + timedelta(days=(i * 1.3) + 2)

            status = DocumentStatus.POSTED if i <= 34 else DocumentStatus.DRAFT
            lines_spec = [(l.product_id, l.quantity, l.unit_price, l.tax_rate) for l in po.lines] if po else [
                (products_map["PROD-TBL-01"].id, 5, Decimal(36000), Decimal(18))
            ]
            tot = sum((line_total(q, pr, tx) for _, q, pr, tx in lines_spec), Decimal("0"))

            if status == DocumentStatus.DRAFT:
                pay_status = PaymentStatus.UNPAID
                amt_paid = Decimal("0")
            elif i % 3 == 1:
                pay_status = PaymentStatus.PAID
                amt_paid = tot
            elif i % 3 == 2:
                pay_status = PaymentStatus.PARTIALLY_PAID
                amt_paid = (tot * Decimal("0.4")).quantize(Decimal("0.01"))
            else:
                pay_status = PaymentStatus.UNPAID
                amt_paid = Decimal("0")

            bill = one(db, PurchaseBill, bill_number=bill_num)
            if not bill:
                bill = PurchaseBill(bill_number=bill_num, contact_id=vend.id, created_by_id=accountant.id,
                                    purchase_order_id=po.id if (po and po.status == DocumentStatus.CONFIRMED) else None,
                                    bill_date=bill_date, status=status, payment_status=pay_status,
                                    total_amount=tot, amount_paid=amt_paid)
                bill.lines = [PurchaseBillLine(product_id=pid, quantity=Decimal(q), unit_price=Decimal(pr),
                                               tax_rate=Decimal(tx), line_total=line_total(q, pr, tx))
                              for pid, q, pr, tx in lines_spec]
                db.add(bill)
                db.flush()
            bills_map[bill_num] = bill

            # Generate Vendor Payment if payment was made (up to 25 payments)
            if amt_paid > 0 and payments_count < 25:
                payments_count += 1
                vpay_num = f"VPAY-2026-0{100 + payments_count}"
                vpay = one(db, VendorPayment, payment_number=vpay_num)
                if not vpay:
                    vpay = VendorPayment(payment_number=vpay_num, purchase_bill_id=bill.id, contact_id=vend.id,
                                         amount=amt_paid, payment_date=bill_date + timedelta(days=4),
                                         status=DocumentStatus.POSTED, idempotency_key=f"seed-vpay-300-{payments_count}",
                                         created_by_id=accountant.id)
                    db.add(vpay)
                    db.flush()

        # 9. Double-Entry Balanced Journal Entries (40 Entries: JE-2026-0101 to JE-2026-0140)
        anl_list = list(analytics_map.values())
        for i in range(1, 41):
            je_num = f"JE-2026-0{100 + i}"
            if one(db, JournalEntry, entry_number=je_num):
                continue
            
            je_date = base_date + timedelta(days=i * 1.5)
            anl = anl_list[(i - 1) % len(anl_list)]

            if i <= 20:
                # Invoice postings: Debit Receivable, Credit Sales Income & GST Payable
                inv_num = f"INV-2026-0{100 + i}"
                inv = invoices_map.get(inv_num)
                if inv and inv.status == DocumentStatus.POSTED:
                    subtotal = (inv.total_amount / Decimal("1.18")).quantize(Decimal("0.01"))
                    tax_amt = inv.total_amount - subtotal
                    
                    entry = JournalEntry(entry_number=je_num, journal_id=sales_journal.id, entry_date=je_date,
                                         narration=f"Sales posting for {inv_num}", status=DocumentStatus.POSTED,
                                         analytic_account_id=anl.id, source_type="SaleInvoice", source_id=inv.id)
                    entry.lines = [
                        JournalEntryLine(account_id=receivable.id, debit=inv.total_amount, credit=Decimal("0"), description="Accounts Receivable"),
                        JournalEntryLine(account_id=sales_income.id, debit=Decimal("0"), credit=subtotal, description="Furniture Sales Income"),
                        JournalEntryLine(account_id=tax_payable.id, debit=Decimal("0"), credit=tax_amt, description="GST Output Payable"),
                    ]
                    db.add(entry)
            elif i <= 35:
                # Bill postings: Debit Purchase Expense & GST Input, Credit Payable
                bill_num = f"BILL-2026-0{100 + (i - 20)}"
                bill = bills_map.get(bill_num)
                if bill and bill.status == DocumentStatus.POSTED:
                    subtotal = (bill.total_amount / Decimal("1.18")).quantize(Decimal("0.01"))
                    tax_amt = bill.total_amount - subtotal

                    entry = JournalEntry(entry_number=je_num, journal_id=purchase_journal.id, entry_date=je_date,
                                         narration=f"Purchase bill posting for {bill_num}", status=DocumentStatus.POSTED,
                                         analytic_account_id=anl.id, source_type="PurchaseBill", source_id=bill.id)
                    entry.lines = [
                        JournalEntryLine(account_id=purchase_expense.id, debit=subtotal, credit=Decimal("0"), description="Furniture Purchase Expense"),
                        JournalEntryLine(account_id=tax_payable.id, debit=tax_amt, credit=Decimal("0"), description="GST Input Credit"),
                        JournalEntryLine(account_id=payable.id, debit=Decimal("0"), credit=bill.total_amount, description="Accounts Payable"),
                    ]
                    db.add(entry)
            else:
                # Miscellaneous Adjustments / Depreciation / Salary
                amt = Decimal(str(i * 2500))
                entry = JournalEntry(entry_number=je_num, journal_id=sales_journal.id, entry_date=je_date,
                                     narration=f"Monthly Operations Adjustment #{i}", status=DocumentStatus.POSTED,
                                     analytic_account_id=anl.id)
                entry.lines = [
                    JournalEntryLine(account_id=bank.id, debit=amt, credit=Decimal("0"), description="Bank Receipt"),
                    JournalEntryLine(account_id=cash.id, debit=Decimal("0"), credit=amt, description="Cash Transfer"),
                ]
                db.add(entry)

        db.flush()

        # 10. Update Document Counters to prevent numbering collisions
        counter_updates = [
            ("SO", 150),
            ("PO", 145),
            ("INV", 145),
            ("BILL", 140),
            ("REC", 130),
            ("PAY", 125),
            ("JE", 140),
        ]
        for prefix, value in counter_updates:
            cnt = one(db, DocumentCounter, prefix=prefix)
            if not cnt:
                db.add(DocumentCounter(prefix=prefix, last_value=value))
            elif cnt.last_value < value:
                cnt.last_value = value

        db.commit()
        print("Successfully seeded 300+ realistic demo entries!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_300()
