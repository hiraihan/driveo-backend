from seed import seed_data
from app.core.config import get_settings


async def _seed(db, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "seed_admin_password", "admin-pass-123")
    await seed_data(db)


async def test_marketplace_endpoints_served(client, db, monkeypatch):
    await _seed(db, monkeypatch)

    spots = await client.get("/marketplace/pickup-spots")
    assert spots.status_code == 200 and len(spots.json()) == 6
    # Diurutkan berdasarkan extra_fee (0 dulu), lalu YIA (fee 100000) di akhir
    spot_ids = {s["id"] for s in spots.json()}
    assert spot_ids == {
        "spot-yia", "spot-tugu", "spot-lempuyangan",
        "spot-malioboro", "spot-sleman", "spot-bantul",
    }
    assert spots.json()[-1]["id"] == "spot-yia"

    vehicles = await client.get("/marketplace/vehicles")
    assert vehicles.status_code == 200 and len(vehicles.json()) == 10

    rentals = await client.get("/marketplace/rentals")
    assert rentals.status_code == 200 and len(rentals.json()) == 4

    disputes = await client.get("/marketplace/disputes")
    assert disputes.status_code == 200 and len(disputes.json()) == 1

    notifications = await client.get("/marketplace/notifications")
    assert notifications.status_code == 200 and len(notifications.json()) == 4


async def test_vehicle_detail_and_by_rental(client, db, monkeypatch):
    await _seed(db, monkeypatch)

    detail = await client.get("/marketplace/vehicles/veh-zenix-01")
    assert detail.status_code == 200
    assert detail.json()["rentalId"] == "rental-tugu"
    assert detail.json()["licensePlate"] == "AB 1001 QZ"

    by_rental = await client.get("/marketplace/vehicles/by-rental/rental-tugu")
    assert by_rental.status_code == 200
    ids = {v["id"] for v in by_rental.json()}
    assert {"veh-zenix-01", "veh-avanza-01"} <= ids

    missing = await client.get("/marketplace/vehicles/nope")
    assert missing.status_code == 404


async def test_dispute_lookup_by_ticket_code(client, db, monkeypatch):
    await _seed(db, monkeypatch)

    by_id = await client.get("/marketplace/disputes/dsp-demo-01")
    assert by_id.status_code == 200
    by_code = await client.get("/marketplace/disputes/DSP-202610-0089")
    assert by_code.status_code == 200
    assert by_id.json()["mediatorVerdict"]["renterRefundAmount"] == 125000


async def test_demo_user_login_and_me(client, db, monkeypatch):
    await _seed(db, monkeypatch)

    r = await client.post(
        "/auth/login",
        data={"username": "budi.santoso@gmail.com", "password": "password123"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "budi.santoso@gmail.com"
    assert body["name"] == "Budi Santoso"
    assert body["phone"] == "081234567890"
    assert body["role"] == "Penyewa"


async def test_demo_roles_login(client, db, monkeypatch):
    await _seed(db, monkeypatch)

    cases = {
        "admin@driveo.id": "Admin",
        "owner@tugurentjogja.com": "Rental",
        "ops@tugurentjogja.com": "STAFF_OPERASIONAL",
        "finance@tugurentjogja.com": "STAFF_KEUANGAN",
        "verifikasi@driveo.id": "TIM_VERIFIKASI",
        "cs@driveo.id": "CUSTOMER_SUPPORT",
        "mediasi@driveo.id": "TIM_MEDIASI",
    }
    for email, role in cases.items():
        r = await client.post(
            "/auth/login",
            data={"username": email, "password": "password123"},
        )
        assert r.status_code == 200, f"login gagal untuk {email}"
        me = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {r.json()['access_token']}"},
        )
        assert me.json()["role"] == role, f"role {email} salah"
