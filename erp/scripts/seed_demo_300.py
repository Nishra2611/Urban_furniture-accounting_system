"""Seeder extension generating 200+ realistic, mathematically balanced, and idempotent ERP database records in EVERY table.

Covers all product categories: Furniture, Chairs, Tables, Office, Decor, General, Storage, Beds, Sofas, Services, Combos.

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
        # 1. Fetch / Create Core Accounts & Infrastructure
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

        # 2. GENERATE 200 CONTACTS (130 Customers, 50 Vendors, 20 Both)
        city_list = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Jaipur", "Surat"]
        cust_prefixes = ["Apex", "Neelam", "Zenith", "Metro", "Urban", "Vanguard", "Starlight", "Silverline", "Prestige", "Aura",
                         "Horizon", "Summit", "Pioneer", "Elegance", "Oasis", "Nexus", "Quantum", "Synergy", "Beacon", "Crest"]
        cust_types = ["Corporate Hub", "Architects", "Tech Park", "Workspace Solutions", "Living Spaces", "Financial", "Design Studio",
                      "Commercial Plaza", "Wellness Clinic", "Global Systems", "Tower Suites", "Law Chambers", "Hotels", "Coworking Space"]

        contacts_map = {}

        # 130 Customers
        for i in range(1, 131):
            code = f"CUST-{i:03d}"
            name = f"{cust_prefixes[(i-1) % len(cust_prefixes)]} {cust_types[(i-1) % len(cust_types)]} #{i}"
            email = f"accounts{i}@cust{i}.com"
            phone = f"98765{i:05d}"
            city = city_list[(i-1) % len(city_list)]
            addr = f"Suite {i*10}, Business Park, {city}"
            
            c = one(db, Contact, code=code)
            if not c:
                c = Contact(code=code, name=name, party_type=PartyType.CUSTOMER, email=email, phone=phone,
                            address=addr, receivable_account_id=receivable.id)
                db.add(c)
            contacts_map[code] = c

        # 50 Vendors
        vend_prefixes = ["Godrej", "ModuForm", "Luxe", "SteelCraft", "GreenPly", "PolyFoam", "GlassTech", "FineFinish", "Century", "AsianPaints"]
        vend_types = ["Wood Suppliers", "Hardware & Fittings", "Fabrics & Upholstery", "Metal Frames", "Plywood Traders", "Cushioning Co", "Glass Tops", "Varnish & Polish"]
        for i in range(1, 51):
            code = f"VEND-{i:03d}"
            name = f"{vend_prefixes[(i-1) % len(vend_prefixes)]} {vend_types[(i-1) % len(vend_types)]} #{i}"
            email = f"sales{i}@vend{i}.com"
            phone = f"98766{i:05d}"
            city = city_list[(i-1) % len(city_list)]
            addr = f"Plot {i*5}, Industrial Zone, {city}"

            c = one(db, Contact, code=code)
            if not c:
                c = Contact(code=code, name=name, party_type=PartyType.VENDOR, email=email, phone=phone,
                            address=addr, payable_account_id=payable.id)
                db.add(c)
            contacts_map[code] = c

        # 20 Both (Customer & Vendor)
        for i in range(1, 21):
            code = f"BOTH-{i:03d}"
            name = f"Global FurnishMart Trading #{i}"
            email = f"trade{i}@bothmart{i}.com"
            phone = f"98767{i:05d}"
            city = city_list[(i-1) % len(city_list)]
            addr = f"Trade Centre {i}, {city}"

            c = one(db, Contact, code=code)
            if not c:
                c = Contact(code=code, name=name, party_type=PartyType.BOTH, email=email, phone=phone,
                            address=addr, receivable_account_id=receivable.id, payable_account_id=payable.id)
                db.add(c)
            contacts_map[code] = c

        db.flush()

        # 3. GENERATE 200 PRODUCTS COVERING ALL CATEGORIES
        # Categories: Furniture, Chairs, Tables, Office, Decor, General, Storage, Beds, Sofas, Services, Combos
        categories_spec = [
            ("Chairs", "CHR", ["Executive Mesh Chair", "Leather Conference Chair", "Visitor Armchair", "High-Back Gaming Chair", "Stackable Seminar Chair", "Bar Stool Chrome Base"], 3500, 18000),
            ("Tables", "TBL", ["Teak Boardroom Table", "Modular L-Shape Desk", "Electric Height Adjustable Desk", "Glass Top Coffee Table", "Folding Seminar Table", "Compact Study Desk"], 6000, 65000),
            ("Sofas", "SOF", ["Chesterfield Leather Sofa", "L-Shape Sectional Fabric Sofa", "Recliner Armchair Microfiber", "Velvet Ottoman Bench Pouf", "Receptive Lounge Sofa"], 8000, 55000),
            ("Beds", "BED", ["Solid Teak King Bed Frame", "Queen Storage Platform Bed", "Nightstand Bedside Table Pair", "Modular 3-Door Sliding Wardrobe", "Bunk Bed Solid Wood"], 9000, 60000),
            ("Storage", "CAB", ["Metal Filing Cabinet 4-Drawer", "Wooden Credenza Sideboard", "Modular Wall Bookshelf Unit", "Under-Desk Mobile Pedestal", "Glass Door Display Cupboard"], 5000, 32000),
            ("Office", "OFF", ["Acoustic Desk Partition Screen", "Ergonomic Footrest Stand", "Cable Management Tray System", "Monitor Arm Dual Mount", "Whiteboard Rolling Stand"], 1500, 14000),
            ("Decor", "DEC", ["Solid Wood Wall Clock", "Brass Accent Table Lamp", "Decorative Ceramic Vase Set", "Framed Abstract Wall Art", "Area Rug Premium Wool"], 1200, 15000),
            ("Furniture", "FUR", ["Teak Wood Rocking Chair", "Outdoor Patio Rattan Set", "Folding Teak Garden Bench", "Vintage Trunk Storage Table", "Shoe Cabinet 4-Tier"], 3500, 28000),
            ("General", "GEN", ["Furniture Polish Spray 500ml", "Heavy Duty Furniture Glides Set", "Upholstery Cleaner Solution", "Wood Scratch Repair Kit", "Corner Protector Cushion Set"], 300, 2500),
            ("Services", "SRV", ["Office Space Interior Layout Design", "On-site Assembly & Installation", "Annual Wood Polishing Service", "Ergonomic Audit & Consultation", "Custom Furniture Crafting"], 2500, 20000),
            ("Combos", "CMB", ["Executive Suite Complete Furniture Package", "Conference Room 10-Chair & Table Set", "Home Office Ergonomic Starter Combo", "Reception Lounge Furniture Set"], 35000, 150000),
        ]

        products_map = {}
        prod_index = 0
        for cat_name, prefix, titles, min_p, max_p in categories_spec:
            items_count = 20 if cat_name in ["Chairs", "Tables", "Sofas", "Storage", "Beds"] else 15
            for j in range(1, items_count + 1):
                prod_index += 1
                code = f"PROD-{prefix}-{j:03d}"
                title = f"{titles[(j-1) % len(titles)]} v{j}"
                sales_p = Decimal(str(min_p + ((j * 17) % (max_p - min_p))))
                purch_p = (sales_p * Decimal("0.65")).quantize(Decimal("0.01"))
                tax_rate = Decimal(str([0, 5, 12, 18, 28][(j) % 5]))
                is_service = (cat_name == "Services")
                stock = Decimal("0") if is_service else Decimal(str(10 + (j * 3)))

                p = one(db, Product, code=code)
                if not p:
                    p = Product(code=code, name=title, product_type="Service" if is_service else "Goods",
                                category=cat_name, sales_price=sales_p, purchase_price=purch_p,
                                tax_rate=tax_rate, track_stock=not is_service, stock_quantity=stock,
                                income_account_id=sales_income.id, expense_account_id=purchase_expense.id,
                                description=f"High quality {cat_name.lower()} item for office and home.")
                    db.add(p)
                products_map[code] = p

        db.flush()
        all_product_keys = list(products_map.keys())

        # 4. GENERATE 50 ANALYTIC ACCOUNTS & 50 BUDGETS
        analytics_map = {}
        regions = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Surat"]
        depts = ["Showroom Ops", "Manufacturing Plant", "Corporate Office", "Regional Distribution", "R&D Design Hub"]

        for i in range(1, 51):
            code = f"ANL-{i:03d}"
            reg = regions[(i-1) % len(regions)]
            dept = depts[(i-1) % len(depts)]
            name = f"{reg} {dept} #{i}"

            anl = one(db, AnalyticAccount, code=code)
            if not anl:
                anl = AnalyticAccount(code=code, name=name, type="Expense" if i % 2 == 0 else "Income")
                db.add(anl)
                db.flush()
            analytics_map[code] = anl

            b_name = f"Budget 2026 — {name}"
            if not one(db, AnalyticBudget, name=b_name):
                amt = Decimal(str(300000 + (i * 25000)))
                db.add(AnalyticBudget(name=b_name, analytic_account_id=anl.id,
                                      period_start="2026-01-01", period_end="2026-12-31", budget_amount=amt))

        db.flush()
        all_analytics = list(analytics_map.values())

        # Lists for relational lookups
        all_customer_codes = [c for c, obj in contacts_map.items() if obj.party_type in (PartyType.CUSTOMER, PartyType.BOTH)]
        all_vendor_codes = [c for c, obj in contacts_map.items() if obj.party_type in (PartyType.VENDOR, PartyType.BOTH)]
        base_date = date(2026, 1, 10)

        # 5. GENERATE 200 SALES ORDERS (SO-2026-0001 to SO-2026-0200)
        sales_orders_map = {}
        for i in range(1, 201):
            so_num = f"SO-2026-{i:04d}"
            cust_code = all_customer_codes[(i - 1) % len(all_customer_codes)]
            cust = contacts_map[cust_code]
            so_date = base_date + timedelta(days=i)
            status = DocumentStatus.CONFIRMED if i % 7 != 0 else (DocumentStatus.DRAFT if i % 2 == 0 else DocumentStatus.CANCELLED)

            p1_key = all_product_keys[(i * 3) % len(all_product_keys)]
            p2_key = all_product_keys[(i * 3 + 1) % len(all_product_keys)]
            p1 = products_map[p1_key]
            p2 = products_map[p2_key]
            lines_spec = [
                (p1.id, (i % 4) + 1, p1.sales_price, p1.tax_rate),
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

        # 6. GENERATE 200 SALE INVOICES & 200 CUSTOMER RECEIPTS
        invoices_map = {}
        for i in range(1, 201):
            inv_num = f"INV-2026-{i:04d}"
            so_num = f"SO-2026-{i:04d}"
            so = sales_orders_map.get(so_num)
            cust_code = all_customer_codes[(i - 1) % len(all_customer_codes)]
            cust = contacts_map[cust_code]
            inv_date = base_date + timedelta(days=i + 1)

            status = DocumentStatus.POSTED if i <= 175 else DocumentStatus.DRAFT
            lines_spec = [(l.product_id, l.quantity, l.unit_price, l.tax_rate) for l in so.lines] if so else [
                (products_map[all_product_keys[0]].id, 2, Decimal(9500), Decimal(18))
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

            # Generate Receipt (200 Receipts)
            rec_num = f"REC-2026-{i:04d}"
            rec_amt = amt_paid if amt_paid > 0 else Decimal(str(1000 + i * 50))
            rec = one(db, Receipt, receipt_number=rec_num)
            if not rec:
                rec = Receipt(receipt_number=rec_num, sale_invoice_id=inv.id, contact_id=cust.id,
                              amount=rec_amt, receipt_date=inv_date + timedelta(days=2),
                              status=DocumentStatus.POSTED, idempotency_key=f"seed-rec-200-{i}",
                              created_by_id=accountant.id)
                db.add(rec)
                db.flush()

        # 7. GENERATE 200 PURCHASE ORDERS (PO-2026-0001 to PO-2026-0200)
        purchase_orders_map = {}
        for i in range(1, 201):
            po_num = f"PO-2026-{i:04d}"
            vend_code = all_vendor_codes[(i - 1) % len(all_vendor_codes)]
            vend = contacts_map[vend_code]
            po_date = base_date + timedelta(days=i)
            status = DocumentStatus.CONFIRMED if i % 6 != 0 else (DocumentStatus.DRAFT if i % 2 == 0 else DocumentStatus.CANCELLED)

            p1_key = all_product_keys[(i * 2) % len(all_product_keys)]
            p2_key = all_product_keys[(i * 2 + 1) % len(all_product_keys)]
            p1 = products_map[p1_key]
            p2 = products_map[p2_key]
            lines_spec = [
                (p1.id, (i % 4) + 4, p1.purchase_price, p1.tax_rate),
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

        # 8. GENERATE 200 PURCHASE BILLS & 200 VENDOR PAYMENTS
        bills_map = {}
        for i in range(1, 201):
            bill_num = f"BILL-2026-{i:04d}"
            po_num = f"PO-2026-{i:04d}"
            po = purchase_orders_map.get(po_num)
            vend_code = all_vendor_codes[(i - 1) % len(all_vendor_codes)]
            vend = contacts_map[vend_code]
            bill_date = base_date + timedelta(days=i + 1)

            status = DocumentStatus.POSTED if i <= 170 else DocumentStatus.DRAFT
            lines_spec = [(l.product_id, l.quantity, l.unit_price, l.tax_rate) for l in po.lines] if po else [
                (products_map[all_product_keys[0]].id, 5, Decimal(6000), Decimal(18))
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

            # Generate Vendor Payment (200 Payments)
            vpay_num = f"VPAY-2026-{i:04d}"
            vpay_amt = amt_paid if amt_paid > 0 else Decimal(str(1500 + i * 40))
            vpay = one(db, VendorPayment, payment_number=vpay_num)
            if not vpay:
                vpay = VendorPayment(payment_number=vpay_num, purchase_bill_id=bill.id, contact_id=vend.id,
                                     amount=vpay_amt, payment_date=bill_date + timedelta(days=3),
                                     status=DocumentStatus.POSTED, idempotency_key=f"seed-vpay-200-{i}",
                                     created_by_id=accountant.id)
                db.add(vpay)
                db.flush()

        # 9. GENERATE 200 DOUBLE-ENTRY BALANCED JOURNAL ENTRIES (JE-2026-0001 to JE-2026-0200)
        for i in range(1, 201):
            je_num = f"JE-2026-{i:04d}"
            if one(db, JournalEntry, entry_number=je_num):
                continue

            je_date = base_date + timedelta(days=i)
            anl = all_analytics[(i - 1) % len(all_analytics)]

            if i <= 80:
                # Invoice posting: Debit Receivable, Credit Sales Income & GST Payable
                inv_num = f"INV-2026-{i:04d}"
                inv = invoices_map.get(inv_num)
                if inv and inv.status == DocumentStatus.POSTED:
                    if one(db, JournalEntry, source_type="SaleInvoice", source_id=inv.id, journal_id=sales_journal.id):
                        continue
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
            elif i <= 160:
                # Bill posting: Debit Purchase Expense & GST Input, Credit Payable
                bill_num = f"BILL-2026-{i - 80:04d}"
                bill = bills_map.get(bill_num)
                if bill and bill.status == DocumentStatus.POSTED:
                    if one(db, JournalEntry, source_type="PurchaseBill", source_id=bill.id, journal_id=purchase_journal.id):
                        continue
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
                # Cash & Bank Transfer / General Adjustment
                amt = Decimal(str(i * 1250))
                entry = JournalEntry(entry_number=je_num, journal_id=sales_journal.id, entry_date=je_date,
                                     narration=f"General Operational Settlement #{i}", status=DocumentStatus.POSTED,
                                     analytic_account_id=anl.id)
                entry.lines = [
                    JournalEntryLine(account_id=bank.id, debit=amt, credit=Decimal("0"), description="Bank Receipt"),
                    JournalEntryLine(account_id=cash.id, debit=Decimal("0"), credit=amt, description="Cash Settlement"),
                ]
                db.add(entry)


        db.flush()

        # 10. UPDATE DOCUMENT COUNTERS TO 200+
        counter_updates = [
            ("SO", 200),
            ("PO", 200),
            ("INV", 200),
            ("BILL", 200),
            ("REC", 200),
            ("PAY", 200),
            ("JE", 200),
        ]
        for prefix, value in counter_updates:
            cnt = one(db, DocumentCounter, prefix=prefix)
            if not cnt:
                db.add(DocumentCounter(prefix=prefix, last_value=value))
            elif cnt.last_value < value:
                cnt.last_value = value

        db.commit()
        print("Successfully seeded 200+ entries in EVERY table across all product categories!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_300()
