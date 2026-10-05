import pytest
from datetime import date
from sqlalchemy.future import select
from app.modules.availability.service import lock_slots, release_slots, block_dates, unblock_date, blocked_vehicle_ids
from app.modules.availability.models import VehicleAvailability
from app.core.errors import Conflict
from tests.factories import make_user, make_rental, make_vehicle, auth_header
from app.core.enums import SlotStatus

@pytest.mark.asyncio
async def test_lock_conflict_on_overlap(db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    
    await lock_slots(db, v.id, date(2026, 12, 1), date(2026, 12, 3), "b1")
    await db.commit()
    
    with pytest.raises(Conflict) as exc:
        await lock_slots(db, v.id, date(2026, 12, 3), date(2026, 12, 5), "b2")
    assert exc.value.code == "SLOT_UNAVAILABLE"
    
    # ensure no partial rows for b2
    res = await db.execute(select(VehicleAvailability).where(VehicleAvailability.booking_id == "b2"))
    assert len(res.scalars().all()) == 0

@pytest.mark.asyncio
async def test_release_only_own_booking(db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    
    await lock_slots(db, v.id, date(2026, 12, 1), date(2026, 12, 2), "b1")
    await block_dates(db, v.id, [date(2026, 12, 3)])
    await db.commit()
    
    released = await release_slots(db, "b1")
    assert released == 2
    
    # 3 Dec should remain
    res = await db.execute(select(VehicleAvailability).where(VehicleAvailability.tanggal == date(2026, 12, 3)))
    assert res.scalars().first().status == SlotStatus.DIBLOKIR.value

@pytest.mark.asyncio
async def test_block_and_unblock_api(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    h = auth_header(u)
    
    res = await client.post(f"/vehicles/{v.id}/blocks", json={"dates": ["2026-12-10", "2026-12-11"]}, headers=h)
    assert res.status_code == 201
    
    res_get = await client.get(f"/vehicles/{v.id}/availability?start=2026-12-10&end=2026-12-11", headers=h)
    data = res_get.json()
    if "data" in data: data = data["data"]
    assert len(data) == 2
    assert data[0]["status"] == "DIBLOKIR"
    
    res_del = await client.delete(f"/vehicles/{v.id}/blocks/2026-12-10", headers=h)
    assert res_del.status_code == 204
    
    res_get2 = await client.get(f"/vehicles/{v.id}/availability?start=2026-12-10&end=2026-12-11", headers=h)
    data2 = res_get2.json()
    if "data" in data2: data2 = data2["data"]
    assert len(data2) == 1
    assert data2[0]["tanggal"] == "2026-12-11"

@pytest.mark.asyncio
async def test_unblock_booked_day_409(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    h = auth_header(u)
    
    await lock_slots(db, v.id, date(2026, 12, 1), date(2026, 12, 1), "b1")
    await db.commit()
    
    res = await client.delete(f"/vehicles/{v.id}/blocks/2026-12-01", headers=h)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "SLOT_BOOKED"

@pytest.mark.asyncio
async def test_blocked_vehicle_ids_range(db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v1 = await make_vehicle(db, r)
    v2 = await make_vehicle(db, r)
    
    await lock_slots(db, v1.id, date(2026, 12, 1), date(2026, 12, 3), "b1")
    await block_dates(db, v2.id, [date(2026, 12, 5)])
    await db.commit()
    
    ids = await blocked_vehicle_ids(db, date(2026, 12, 2), date(2026, 12, 4))
    assert v1.id in ids
    assert v2.id not in ids
