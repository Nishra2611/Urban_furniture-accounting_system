from tests.conftest import create_admin


def _setup_customer_and_product(client, headers):
    contact_resp = client.post("/api/v1/contacts", headers=headers, json={
        "code": "CUST001", "name": "ABC Ltd", "party_type": "Customer",
    })
    assert contact_resp.status_code == 201, contact_resp.text
    product_resp = client.post("/api/v1/products", headers=headers, json={
        "code": "PROD001", "name": "Office Chair", "sales_price": "1000.00", "tax_rate": "10",
    })
    assert product_resp.status_code == 201, product_resp.text
    return contact_resp.json()["id"], product_resp.json()["id"]


def test_full_sales_order_to_receipt_flow(client, db_session):
    headers = create_admin(client, db_session)
    contact_id, product_id = _setup_customer_and_product(client, headers)

    # Create + confirm sales order
    so_resp = client.post("/api/v1/sales/orders", headers=headers, json={
        "contact_id": contact_id, "order_date": "2026-09-01",
        "lines": [{"product_id": product_id, "quantity": "2"}],
    })
    assert so_resp.status_code == 201, so_resp.text
    so = so_resp.json()
    assert so["total_amount"] == "2200.00"  # 2 * 1000 * 1.10

    confirm_so = client.post(f"/api/v1/sales/orders/{so['id']}/confirm", headers=headers)
    assert confirm_so.status_code == 200
    assert confirm_so.json()["status"] == "Confirmed"

    # Convert to invoice
    inv_resp = client.post("/api/v1/sales/invoices", headers=headers, json={
        "contact_id": contact_id, "invoice_date": "2026-09-02", "sales_order_id": so["id"],
    })
    assert inv_resp.status_code == 201, inv_resp.text
    invoice = inv_resp.json()
    assert invoice["total_amount"] == "2200.00"

    # Cannot invoice the same order twice
    dup_resp = client.post("/api/v1/sales/invoices", headers=headers, json={
        "contact_id": contact_id, "invoice_date": "2026-09-02", "sales_order_id": so["id"],
    })
    assert dup_resp.status_code == 409

    confirm_inv = client.post(f"/api/v1/sales/invoices/{invoice['id']}/confirm", headers=headers)
    assert confirm_inv.status_code == 200, confirm_inv.text
    assert confirm_inv.json()["status"] == "Confirmed"

    # Record full receipt
    receipt_resp = client.post("/api/v1/sales/receipts", headers=headers, json={
        "sale_invoice_id": invoice["id"], "amount": "2200.00", "receipt_date": "2026-09-03",
        "idempotency_key": "receipt-key-1",
    })
    assert receipt_resp.status_code == 201, receipt_resp.text

    # Duplicate submission with the same idempotency key must not double-process
    dup_receipt = client.post("/api/v1/sales/receipts", headers=headers, json={
        "sale_invoice_id": invoice["id"], "amount": "2200.00", "receipt_date": "2026-09-03",
        "idempotency_key": "receipt-key-1",
    })
    assert dup_receipt.status_code == 201
    assert dup_receipt.json()["id"] == receipt_resp.json()["id"]

    # Verify journal entries are balanced
    from app.models.accounting import JournalEntry, JournalEntryLine
    entries = db_session.query(JournalEntry).all()
    assert len(entries) == 2  # one for invoice confirm, one for receipt
    for entry in entries:
        lines = db_session.query(JournalEntryLine).filter(JournalEntryLine.entry_id == entry.id).all()
        total_debit = sum(l.debit for l in lines)
        total_credit = sum(l.credit for l in lines)
        assert total_debit == total_credit


def test_overpayment_rejected(client, db_session):
    headers = create_admin(client, db_session)
    contact_id, product_id = _setup_customer_and_product(client, headers)

    inv_resp = client.post("/api/v1/sales/invoices", headers=headers, json={
        "contact_id": contact_id, "invoice_date": "2026-09-02",
        "lines": [{"product_id": product_id, "quantity": "1"}],
    })
    invoice = inv_resp.json()
    client.post(f"/api/v1/sales/invoices/{invoice['id']}/confirm", headers=headers)

    over_resp = client.post("/api/v1/sales/receipts", headers=headers, json={
        "sale_invoice_id": invoice["id"], "amount": "9999.00", "receipt_date": "2026-09-03",
    })
    assert over_resp.status_code == 422


def test_inactive_product_blocked_from_new_transaction(client, db_session):
    headers = create_admin(client, db_session)
    contact_id, product_id = _setup_customer_and_product(client, headers)
    client.post(f"/api/v1/products/{product_id}/deactivate", headers=headers)

    resp = client.post("/api/v1/sales/orders", headers=headers, json={
        "contact_id": contact_id, "order_date": "2026-09-01",
        "lines": [{"product_id": product_id, "quantity": "1"}],
    })
    assert resp.status_code == 422
