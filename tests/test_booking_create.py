import pytest
from datetime import date, timedelta
from tests.factories import make_user, auth_header, make_rental, make_vehicle, make_listing, make_verified_user
from app.core.time import today_wib

@pytest.mark.asyncio
async def test_create_booking_201_server_priced(client, db):
    u = await make_verified_user(db)
    r = await make_rental(db, u) # this makes u the rental owner, wait, let's use another user for renting
    
    owner = await make_user(db)
    rental = await make_rental(db, owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    
    payload = {
        "listing_id": listing.id,
        "tanggal_mulai": today_wib().isoformat(),
        "tanggal_selesai": (today_wib() + timedelta(days=2)).isoformat()
    }
    
    # extra field should be rejected (like client sending total_nilai)
    res_bad = await client.post("/bookings", json={**payload, "total_nilai": 100}, headers=auth_header(u))
    assert res_bad.status_code == 422
    
    res = await client.post("/bookings", json=payload, headers=auth_header(u))
    assert res.status_code == 201
    data = res.json()
    assert data["total_nilai"] == listing.harga_all_in * 3
    assert data["booking_state"] == "MENUNGGU_DP"

@pytest.mark.asyncio
async def test_requires_kyc(client, db):
    u = await make_user(db) # not verified
    res = await client.post("/bookings", json={"listing_id": "dummy", "tanggal_mulai": "2030-01-01", "tanggal_selesai": "2030-01-01"}, headers=auth_header(u))
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "KYC_REQUIRED"

@pytest.mark.asyncio
async def test_past_date_422(client, db):
    u = await make_verified_user(db)
    past = (today_wib() - timedelta(days=1)).isoformat()
    res = await client.post("/bookings", json={"listing_id": "dummy", "tanggal_mulai": past, "tanggal_selesai": past}, headers=auth_header(u))
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "DATE_IN_PAST"

@pytest.mark.asyncio
async def test_reversed_dates_422(client, db):
    u = await make_verified_user(db)
    t = today_wib()
    res = await client.post("/bookings", json={"listing_id": "dummy", "tanggal_mulai": (t + timedelta(days=2)).isoformat(), "tanggal_selesai": t.isoformat()}, headers=auth_header(u))
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "DATE_RANGE_INVALID"

@pytest.mark.asyncio
async def test_bad_promo_422(client, db):
    u = await make_verified_user(db)
    owner = await make_user(db)
    rental = await make_rental(db, owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    t = today_wib() + timedelta(days=10)
    res = await client.post("/bookings", json={"listing_id": listing.id, "tanggal_mulai": t.isoformat(), "tanggal_selesai": (t+timedelta(days=1)).isoformat(), "promo_code": "INVALID"}, headers=auth_header(u))
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "PROMO_INVALID"

@pytest.mark.asyncio
async def test_overlap_one_boundary_day_409_adjacent_ok(client, db):
    u = await make_verified_user(db)
    owner = await make_user(db)
    rental = await make_rental(db, owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    
    t = today_wib() + timedelta(days=10)
    
    payload1 = {
        "listing_id": listing.id,
        "tanggal_mulai": t.isoformat(),
        "tanggal_selesai": (t + timedelta(days=2)).isoformat() # say Dec 1 to 3
    }
    await client.post("/bookings", json=payload1, headers=auth_header(u))
    
    # Overlap boundary day: Dec 3 to 5 should fail because Dec 3 is booked
    payload2 = {
        "listing_id": listing.id,
        "tanggal_mulai": (t + timedelta(days=2)).isoformat(),
        "tanggal_selesai": (t + timedelta(days=4)).isoformat()
    }
    res_overlap = await client.post("/bookings", json=payload2, headers=auth_header(u))
    assert res_overlap.status_code == 409
    assert res_overlap.json()["error"]["code"] == "SLOT_UNAVAILABLE"
    
    # Adjacent range: Dec 4 to 5 should pass
    payload3 = {
        "listing_id": listing.id,
        "tanggal_mulai": (t + timedelta(days=3)).isoformat(),
        "tanggal_selesai": (t + timedelta(days=4)).isoformat()
    }
    res_adj = await client.post("/bookings", json=payload3, headers=auth_header(u))
    assert res_adj.status_code == 201

@pytest.mark.asyncio
async def test_audit_booking_created(client, db):
    u = await make_verified_user(db)
    owner = await make_user(db)
    rental = await make_rental(db, owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    
    t = today_wib() + timedelta(days=20)
    payload = {
        "listing_id": listing.id,
        "tanggal_mulai": t.isoformat(),
        "tanggal_selesai": t.isoformat()
    }
    await client.post("/bookings", json=payload, headers=auth_header(u))
    
    from sqlalchemy import select
    from app.modules.audit.models import AuditLog
    # Check audit log
    log = (await db.execute(select(AuditLog).where(AuditLog.event_name == "BOOKING_CREATED"))).scalars().first()
    assert log is not None
    assert log.actor_id == u.id
