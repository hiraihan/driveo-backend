import pytest
from datetime import date
from tests.factories import make_user, make_rental, make_vehicle, make_listing
from app.core.enums import ListingStatus
from app.modules.availability.service import lock_slots

@pytest.mark.asyncio
async def test_excludes_booked_vehicle_in_range(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    l = await make_listing(db, v)
    
    await lock_slots(db, v.id, date(2026, 12, 2), date(2026, 12, 2), "b1")
    await db.commit()
    
    # 1-3 Dec should exclude
    res = await client.get("/search?start_date=2026-12-01&end_date=2026-12-03")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 0
    
    # 4-5 Dec should include
    res2 = await client.get("/search?start_date=2026-12-04&end_date=2026-12-05")
    assert len(res2.json()["data"]) == 1

@pytest.mark.asyncio
async def test_location_filter(client, db):
    u1 = await make_user(db)
    r1 = await make_rental(db, u1)
    r1.alamat = "Jakarta Selatan"
    v1 = await make_vehicle(db, r1)
    await make_listing(db, v1)
    
    u2 = await make_user(db)
    r2 = await make_rental(db, u2)
    r2.alamat = "Bandung"
    v2 = await make_vehicle(db, r2)
    await make_listing(db, v2)
    
    await db.commit()
    
    res = await client.get("/search?lokasi=jakarta")
    assert len(res.json()["data"]) == 1

@pytest.mark.asyncio
async def test_sort_price_asc(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v1 = await make_vehicle(db, r, tarif_dasar=500000)
    await make_listing(db, v1)
    v2 = await make_vehicle(db, r, tarif_dasar=200000)
    await make_listing(db, v2)
    
    res = await client.get("/search?sort=price_asc")
    data = res.json()["data"]
    assert len(data) >= 2
    assert data[0]["harga_all_in"] <= data[-1]["harga_all_in"]

@pytest.mark.asyncio
async def test_pagination_meta(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    for _ in range(25):
        v = await make_vehicle(db, r)
        await make_listing(db, v)
    
    res = await client.get("/search?page=3&page_size=10")
    assert res.status_code == 200
    meta = res.json()["pagination"]
    assert meta["total_items"] >= 25
    assert len(res.json()["data"]) > 0

@pytest.mark.asyncio
async def test_incomplete_range_422(client):
    res = await client.get("/search?start_date=2026-12-01")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "DATE_RANGE_INCOMPLETE"
    
    res2 = await client.get("/search?start_date=2026-12-05&end_date=2026-12-01")
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "DATE_RANGE_INVALID"
