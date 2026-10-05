import pytest
from tests.factories import make_user, make_admin, auth_header
from app.core.enums import UserRole

@pytest.mark.asyncio
async def test_admin_create_promo(client, db):
    admin = await make_admin(db)
    headers = auth_header(admin, UserRole.ADMIN)
    
    payload = {
        "code": "SUMMER2026",
        "discount_percent": 15,
        "max_discount_amount": 100000,
        "valid_until": "2026-12-31"
    }
    
    res = await client.post("/admin/promos", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    if "data" in data:
        data = data["data"]
    assert data["code"] == "SUMMER2026"
    assert data["discount_percent"] == 15
    assert data["max_discount_amount"] == 100000

@pytest.mark.asyncio
async def test_admin_create_membership(client, db):
    admin = await make_admin(db)
    headers = auth_header(admin, UserRole.ADMIN)
    
    payload = {
        "name": "PREMIUM",
        "price": 500000,
        "max_vehicles": 10,
        "max_staff": 5
    }
    
    res = await client.post("/admin/memberships", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    if "data" in data:
        data = data["data"]
    assert data["name"] == "PREMIUM"
    assert data["price"] == 500000

@pytest.mark.asyncio
async def test_non_admin_cannot_create_promo(client, db):
    user = await make_user(db)
    headers = auth_header(user, UserRole.PENYEWA)
    
    payload = {
        "code": "HACKER",
        "discount_percent": 99,
        "max_discount_amount": 1000000,
        "valid_until": "2026-12-31"
    }
    
    res = await client.post("/admin/promos", json=payload, headers=headers)
    assert res.status_code == 403
