import pytest
from app.core.enums import UserRole, RentalStatus
from tests.factories import make_user, make_admin, auth_header, make_rental
from app.modules.audit.models import AuditLog
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_onboard_promotes_to_rental(client, db):
    user = await make_user(db)
    h = auth_header(user)
    payload = {
        "nama_usaha": "Test Rental",
        "nib": "1234567890",
        "alamat": "Jl. Test",
        "kontak": "0812345678",
        "payout_account": "123456"
    }
    res = await client.post("/rentals/onboard", json=payload, headers=h)
    assert res.status_code == 201
    
    # check role promoted
    me = await client.get("/users/me", headers=h)
    assert me.json()["role"] == "Rental"
    data = res.json()
    if "data" in data: data = data["data"]
    assert data["status_verifikasi"] == RentalStatus.MENUNGGU.value

@pytest.mark.asyncio
async def test_onboard_twice_409(client, db):
    user = await make_user(db)
    h = auth_header(user)
    payload = {
        "nama_usaha": "Test Rental",
        "nib": "1234567890",
        "alamat": "Jl. Test",
        "kontak": "0812345678",
        "payout_account": "123456"
    }
    await client.post("/rentals/onboard", json=payload, headers=h)
    res = await client.post("/rentals/onboard", json=payload, headers=h)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_RENTAL_STAFF"

@pytest.mark.asyncio
async def test_verify_rejects_unknown_status(client, db):
    admin = await make_admin(db)
    h = auth_header(admin)
    user = await make_user(db)
    rental = await make_rental(db, user, status=RentalStatus.MENUNGGU)
    
    res = await client.post(f"/rentals/{rental.id}/verify", json={"status": "TERSERAH"}, headers=h)
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_verify_requires_admin(client, db):
    user = await make_user(db)
    rental = await make_rental(db, user, status=RentalStatus.MENUNGGU)
    h = auth_header(user)
    
    res = await client.post(f"/rentals/{rental.id}/verify", json={"status": RentalStatus.LOLOS.value}, headers=h)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_verify_writes_audit(client, db):
    admin = await make_admin(db)
    h = auth_header(admin)
    user = await make_user(db)
    rental = await make_rental(db, user, status=RentalStatus.MENUNGGU)
    
    res = await client.post(f"/rentals/{rental.id}/verify", json={"status": RentalStatus.LOLOS.value}, headers=h)
    assert res.status_code == 200
    
    stmt = select(AuditLog).where(AuditLog.event_name == "RENTAL_VERIFIED")
    row = (await db.execute(stmt)).scalar_one()
    assert row.actor_id == admin.id

@pytest.mark.asyncio
async def test_payout_not_exposed(client, db):
    user = await make_user(db)
    rental = await make_rental(db, user)
    
    res = await client.get(f"/rentals/{rental.id}")
    assert res.status_code == 200
    data = res.json()
    if "data" in data: data = data["data"]
    assert "payout_account" not in data
