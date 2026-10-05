import pytest
from tests.factories import make_user, auth_header, make_rental, make_vehicle
from app.core.enums import VehicleStatus
from app.modules.vehicle.models import Vehicle

@pytest.mark.asyncio
async def test_create_uses_staff_rental(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    
    payload = {
        "jenis": "Mobil",
        "merk": "Honda",
        "tipe": "Brio",
        "plat_nomor": "D 1234 XY",
        "tarif_dasar": 300000
    }
    h = auth_header(u)
    res = await client.post("/vehicles", json=payload, headers=h)
    assert res.status_code == 201
    
    data = res.json()
    if "data" in data: data = data["data"]
    assert data["rental_id"] == r.id

@pytest.mark.asyncio
async def test_body_rental_id_rejected(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    h = auth_header(u)
    payload = {
        "rental_id": "hack",
        "jenis": "Mobil",
        "merk": "Honda",
        "tipe": "Brio",
        "plat_nomor": "D 1234 XZ",
        "tarif_dasar": 300000
    }
    res = await client.post("/vehicles", json=payload, headers=h)
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_non_positive_tarif(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    h = auth_header(u)
    payload = {
        "jenis": "Mobil",
        "merk": "Honda",
        "tipe": "Brio",
        "plat_nomor": "D 1234 XX",
        "tarif_dasar": 0
    }
    res = await client.post("/vehicles", json=payload, headers=h)
    assert res.status_code == 422

@pytest.mark.asyncio
async def test_quota(client, db, monkeypatch):
    from app.core.config import get_settings
    s = get_settings()
    # Mock default limit for this test
    monkeypatch.setattr(s, "default_max_vehicles", 2)
    
    u = await make_user(db)
    r = await make_rental(db, u)
    await make_vehicle(db, r)
    await make_vehicle(db, r)
    
    payload = {
        "jenis": "Mobil", "merk": "H", "tipe": "B", "plat_nomor": "D 1234 A", "tarif_dasar": 300000
    }
    h = auth_header(u)
    res = await client.post("/vehicles", json=payload, headers=h)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "VEHICLE_LIMIT_REACHED"

@pytest.mark.asyncio
async def test_patch_other_rental_403(client, db):
    u1 = await make_user(db)
    r1 = await make_rental(db, u1)
    v1 = await make_vehicle(db, r1)
    
    u2 = await make_user(db)
    r2 = await make_rental(db, u2)
    
    h2 = auth_header(u2)
    res = await client.patch(f"/vehicles/{v1.id}", json={"merk": "Hacked"}, headers=h2)
    assert res.status_code == 403

@pytest.mark.asyncio
async def test_soft_delete_hides(client, db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    h = auth_header(u)
    
    res = await client.delete(f"/vehicles/{v.id}", headers=h)
    assert res.status_code == 204
    
    res_get = await client.get(f"/vehicles/{v.id}")
    assert res_get.status_code == 404
    
    res_list = await client.get(f"/vehicles?rental_id={r.id}")
    assert res_list.status_code == 200
    data = res_list.json()
    if "data" in data: data = data["data"]
    assert len(data) == 0
