from tests.conftest import create_admin, auth_headers
from app.models.enums import UserRole
from app.models.user import User


def test_signup_success(client):
    resp = client.post("/api/v1/auth/signup", json={
        "login_id": "user0001", "email": "u1@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    assert resp.status_code == 201, resp.text
    assert resp.json()["role"] == "User"


def test_signup_rejects_weak_password(client):
    resp = client.post("/api/v1/auth/signup", json={
        "login_id": "user0002", "email": "u2@test.com",
        "password": "weakpass", "re_password": "weakpass",
    })
    assert resp.status_code == 422


def test_signup_rejects_mismatched_confirmation(client):
    resp = client.post("/api/v1/auth/signup", json={
        "login_id": "user0003", "email": "u3@test.com",
        "password": "Str0ng!Pass", "re_password": "Different!1",
    })
    assert resp.status_code == 422


def test_signup_rejects_short_login_id(client):
    resp = client.post("/api/v1/auth/signup", json={
        "login_id": "abc", "email": "u4@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    assert resp.status_code == 422


def test_duplicate_login_id_rejected(client):
    payload = {
        "login_id": "dupuser1", "email": "dup1@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    }
    assert client.post("/api/v1/auth/signup", json=payload).status_code == 201
    payload2 = dict(payload, email="dup2@test.com")
    resp = client.post("/api/v1/auth/signup", json=payload2)
    assert resp.status_code == 409


def test_login_invalid_credentials_generic_error(client):
    resp = client.post("/api/v1/auth/login", json={"login_id": "nouser01", "password": "whatever"})
    assert resp.status_code == 401
    assert "Invalid Login Id or Password" in resp.text


def test_signup_cannot_choose_role(client):
    # Signup schema has no role field at all - a normal user cannot self-elevate.
    resp = client.post("/api/v1/auth/signup", json={
        "login_id": "sneaky01", "email": "sneaky@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
        "role": "Administrator",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "User"


def test_create_user_requires_accountant_or_admin(client, db_session):
    # A plain User cannot create other users.
    client.post("/api/v1/auth/signup", json={
        "login_id": "plainusr1", "email": "plain1@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    headers = auth_headers(client, "plainusr1", "Str0ng!Pass")
    resp = client.post("/api/v1/auth/create-user", headers=headers, json={
        "name": "New Guy", "login_id": "newuser01", "email": "new@test.com",
        "role": "Administrator", "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    assert resp.status_code == 403


def test_accountant_cannot_manage_users(client, db_session):
    client.post("/api/v1/auth/signup", json={
        "login_id": "acctusr1", "email": "acctusr@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    user = db_session.query(User).filter_by(login_id="acctusr1").first()
    user.role = UserRole.ACCOUNTANT
    db_session.commit()
    headers = auth_headers(client, "acctusr1", "Str0ng!Pass")
    assert client.get("/api/v1/auth/users", headers=headers).status_code == 403
    assert client.post("/api/v1/auth/create-user", headers=headers, json={
        "name": "New Guy", "login_id": "newuser02", "email": "new2@test.com",
        "role": "User", "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    }).status_code == 403


def test_contact_user_cannot_access_staff_or_portal_without_contact(client):
    client.post("/api/v1/auth/signup", json={
        "login_id": "portalusr1", "email": "portalusr@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    headers = auth_headers(client, "portalusr1", "Str0ng!Pass")
    assert client.get("/api/v1/dashboard", headers=headers).status_code == 403
    assert client.get("/api/v1/portal/my-invoices", headers=headers).status_code == 422


def test_admin_can_create_accountant(client, db_session):
    headers = create_admin(client, db_session)
    resp = client.post("/api/v1/auth/create-user", headers=headers, json={
        "name": "Accountant One", "login_id": "acct0001", "email": "acct@test.com",
        "role": "Accountant", "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    assert resp.status_code == 201, resp.text
    assert resp.json()["role"] == "Accountant"


def test_account_locks_after_failed_attempts(client):
    client.post("/api/v1/auth/signup", json={
        "login_id": "locktest1", "email": "lock@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"login_id": "locktest1", "password": "wrong"})
    resp = client.post("/api/v1/auth/login", json={"login_id": "locktest1", "password": "Str0ng!Pass"})
    assert resp.status_code == 423


def test_logout_revokes_token(client):
    client.post("/api/v1/auth/signup", json={
        "login_id": "logouttst", "email": "logout@test.com",
        "password": "Str0ng!Pass", "re_password": "Str0ng!Pass",
    })
    headers = auth_headers(client, "logouttst", "Str0ng!Pass")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    client.post("/api/v1/auth/logout", headers=headers)
    resp2 = client.get("/api/v1/auth/me", headers=headers)
    assert resp2.status_code == 401
