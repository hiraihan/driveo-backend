import jwt
import pytest
from tests.factories import make_user, auth_header
from app.core.enums import UserRole

async def test_register_always_penyewa(client):
    r = await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    assert r.status_code == 201 and r.json()["role"] == "Penyewa"

async def test_register_rejects_role_field(client):
    r = await client.post("/auth/register", json={"email": "a@x.com", "password": "password1", "role_name": "Admin"})
    assert r.status_code == 422

async def test_register_duplicate_email(client):
    body = {"email": "a@x.com", "password": "password1"}
    await client.post("/auth/register", json=body)
    r = await client.post("/auth/register", json=body)
    assert r.status_code == 409 and r.json()["error"]["code"] == "EMAIL_TAKEN"

async def test_register_short_password(client):
    assert (await client.post("/auth/register", json={"email": "a@x.com", "password": "123"})).status_code == 422

async def test_login_and_refresh(client):
    await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    tok = (await client.post("/auth/login", data={"username": "a@x.com", "password": "password1"})).json()
    r = await client.post("/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 200 and r.json()["access_token"]
    r = await client.post("/auth/refresh", json={"refresh_token": tok["access_token"]})
    assert r.status_code == 401

async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    r = await client.post("/auth/login", data={"username": "a@x.com", "password": "nope-nope"})
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"

async def test_forged_token_rejected(client, db):
    u = await make_user(db)
    from app.core.config import get_settings
    settings = get_settings()
    forged = jwt.encode({"sub": u.id, "role": "Admin", "type": "access"}, "test_secret_key", algorithm="HS256")
    assert (await client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})).status_code == 401

async def test_inactive_user_rejected(client, db):
    u = await make_user(db, is_active=False)
    assert (await client.get("/users/me", headers=auth_header(u))).status_code == 401

async def test_role_comes_from_db_not_token(client, db):
    u = await make_user(db)  # Penyewa
    r = await client.post("/admin/promos", headers=auth_header(u, role=UserRole.ADMIN),
                          json={"code": "X", "discount_percent": 10, "max_discount_amount": 1, "valid_until": "2030-01-01"})
    assert r.status_code == 403

async def test_me_returns_role_name(client, db):
    u = await make_user(db)
    assert (await client.get("/users/me", headers=auth_header(u))).json()["role"] == "Penyewa"
