import pytest
from tests.factories import make_user, auth_header, make_rental, make_vehicle, make_listing
from app.core.enums import RentalStatus, VehicleStatus, ListingStatus
from datetime import timedelta
from app.core.time import utcnow
from app.modules.listing.service import is_stale

def test_is_stale():
    from app.core.config import get_settings
    s = get_settings()
    now = utcnow()
    assert is_stale(now, now) is False
    assert is_stale(now - timedelta(days=s.listing_stale_days + 1), now) is True

@pytest.mark.asyncio
async def test_penyewa_cannot_create(client, db):
    u = await make_user(db)
    h = auth_header(u)
    payload = {"vehicle_id": "123", "judul": "J", "biaya_tambahan": 0}
    res = await client.post("/listings", json=payload, headers=h)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_ghost_vehicle_404(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    h = auth_header(u)
    payload = {"vehicle_id": "ghost_id", "judul": "J", "biaya_tambahan": 0}
    res = await client.post("/listings", json=payload, headers=h)
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_price_computed(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r, tarif_dasar=300000)
    h = auth_header(u)
    
    # Body with harga_all_in -> 422
    payload_bad = {"vehicle_id": v.id, "judul": "J", "biaya_tambahan": 50000, "harga_all_in": 350000}
    res_bad = await client.post("/listings", json=payload_bad, headers=h)
    assert res_bad.status_code == 422
    
    # Correct body
    payload = {"vehicle_id": v.id, "judul": "J", "biaya_tambahan": 50000}
    res = await client.post("/listings", json=payload, headers=h)
    assert res.status_code == 201
    
    data = res.json()
    if "data" in data: data = data["data"]
    assert data["harga_all_in"] == 350000

@pytest.mark.asyncio
async def test_publish_requires_verified_rental(client, db):
    u = await make_user(db)
    r = await make_rental(db, u, status=RentalStatus.MENUNGGU)
    v = await make_vehicle(db, r)
    l = await make_listing(db, v, status=ListingStatus.DRAFT)
    h = auth_header(u)
    
    res = await client.post(f"/listings/{l.id}/publish", headers=h)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "RENTAL_NOT_VERIFIED"
    
    # update rental to LOLOS and vehicle to INACTIVE
    r.status_verifikasi = RentalStatus.LOLOS.value
    v.status = VehicleStatus.NONAKTIF.value
    await db.commit()
    
    res2 = await client.post(f"/listings/{l.id}/publish", headers=h)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "VEHICLE_INACTIVE"

