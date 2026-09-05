from tests.conftest import create_admin, auth_headers


def test_user_cannot_see_other_customers_invoice(client, db_session):
    admin_headers = create_admin(client, db_session)

    # Two customers, each with their own portal user, each with an invoice.
    c1 = client.post("/api/v1/contacts", headers=admin_headers, json={
        "code": "CUSTA", "name": "Customer A", "party_type": "Customer",
    }).json()
    c2 = client.post("/api/v1/contacts", headers=admin_headers, json={
        "code": "CUSTB", "name": "Customer B", "party_type": "Customer",
    }).json()
    product = client.post("/api/v1/products", headers=admin_headers, json={
        "code": "PRODX", "name": "Widget", "sales_price": "500.00",
    }).json()

    inv_a = client.post("/api/v1/sales/invoices", headers=admin_headers, json={
        "contact_id": c1["id"], "invoice_date": "2026-09-01",
        "lines": [{"product_id": product["id"], "quantity": "1"}],
    }).json()
    client.post(f"/api/v1/sales/invoices/{inv_a['id']}/confirm", headers=admin_headers)

    # Create a portal user (role User) and manually link it to customer A via the ORM,
    # since Signup never accepts a contact linkage from the client.
    from app.models.user import User
    signup_resp = client.post("/api/v1/auth/signup", json={
        "login_id": "custauser", "email": "custa@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    user = db_session.query(User).filter(User.login_id == "custauser").first()
    user.contact_id = c1["id"]
    db_session.commit()

    user_headers = auth_headers(client, "custauser", "Str0ng!Pass")

    # This user can see their own invoice.
    my_invoices = client.get("/api/v1/portal/my-invoices", headers=user_headers)
    assert my_invoices.status_code == 200
    assert len(my_invoices.json()) == 1

    # But cannot pay/view customer B's invoice, even by guessing an ID.
    inv_b = client.post("/api/v1/sales/invoices", headers=admin_headers, json={
        "contact_id": c2["id"], "invoice_date": "2026-09-01",
        "lines": [{"product_id": product["id"], "quantity": "1"}],
    }).json()
    client.post(f"/api/v1/sales/invoices/{inv_b['id']}/confirm", headers=admin_headers)

    pay_resp = client.post("/api/v1/portal/pay", headers=user_headers, json={
        "sale_invoice_id": inv_b["id"], "amount": "500.00", "receipt_date": "2026-09-02",
    })
    assert pay_resp.status_code == 404


def test_user_cannot_access_master_data(client, db_session):
    client.post("/api/v1/auth/signup", json={
        "login_id": "plainonly", "email": "plainonly@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    headers = auth_headers(client, "plainonly", "Str0ng!Pass")
    resp = client.get("/api/v1/contacts", headers=headers)
    assert resp.status_code == 403
