import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from app.core.enums import RentalStatus, ListingStatus, UserRole
from app.core.time import today_wib
from tests.factories import make_user

async def test_e2e_rental_flow(client: AsyncClient, db):
    # 1. Users register
    r_penyewa = await client.post("/auth/register", json={"email": "penyewa@test.com", "password": "password1"})
    assert r_penyewa.status_code == 201
    token_penyewa = (await client.post("/auth/login", data={"username": "penyewa@test.com", "password": "password1"})).json()["access_token"]
    hp = {"Authorization": f"Bearer {token_penyewa}"}

    r_rental_user = await client.post("/auth/register", json={"email": "rental@test.com", "password": "password1"})
    token_rental = (await client.post("/auth/login", data={"username": "rental@test.com", "password": "password1"})).json()["access_token"]
    hr = {"Authorization": f"Bearer {token_rental}"}

    # Admin user
    admin_user = await make_user(db, role=UserRole.ADMIN, email="admin@driveo.com")
    token_admin = (await client.post("/auth/login", data={"username": "admin@driveo.com", "password": "password"})).json()["access_token"]
    ha = {"Authorization": f"Bearer {token_admin}"}

    # 2. Penyewa eKYC
    # Using dummy endpoints for E2E
    # Let's bypass eKYC upload and mock verification for penyewa
    from app.modules.verification.service import VerificationService
    from app.modules.verification.models import Verification
    v = Verification(id="v1", user_id=r_penyewa.json()["id"], status="TERVERIFIKASI")
    db.add(v)
    await db.commit()

    # 3. Rental user onboards
    r = await client.post("/rentals/onboard", headers=hr, json={
        "nama_usaha": "Rental Makmur",
        "nib": "12345",
        "alamat": "Jl. Sudirman",
        "kontak": "0812",
        "payout_account": "BCA 123"
    })
    assert r.status_code == 201
    rental_id = r.json()["id"]

    # Refresh rental token because role changed
    token_rental = (await client.post("/auth/login", data={"username": "rental@test.com", "password": "password1"})).json()["access_token"]
    hr = {"Authorization": f"Bearer {token_rental}"}

    # 4. Admin verifies rental
    r = await client.post(f"/rentals/{rental_id}/verify", headers=ha, json={"status": "LOLOS", "alasan": None})
    assert r.status_code == 200

    # 5. Rental adds vehicle
    r = await client.post("/vehicles", headers=hr, json={
        "jenis": "Mobil", "merk": "Toyota", "tipe": "Avanza",
        "plat_nomor": "B 1234 CD", "tarif_dasar": 300000
    })
    assert r.status_code == 201
    vehicle_id = r.json()["id"]

    # 6. Rental creates and publishes listing
    r = await client.post("/listings", headers=hr, json={
        "vehicle_id": vehicle_id, "judul": "Avanza Mantap", "biaya_tambahan": 50000
    })
    listing_id = r.json()["id"]
    r = await client.post(f"/listings/{listing_id}/publish", headers=hr)
    assert r.status_code == 200

    # 7. Penyewa searches
    start = today_wib()
    end = start + timedelta(days=2)
    r = await client.get(f"/search?start_date={start}&end_date={end}")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1
    
    # 8. Books 3 days
    r = await client.post("/bookings", headers=hp, json={
        "listing_id": listing_id, "tanggal_mulai": str(start), "tanggal_selesai": str(end)
    })
    assert r.status_code == 201
    booking_id = r.json()["id"]

    # 9. DP intent + simulate
    r = await client.post(f"/bookings/{booking_id}/payments", headers=hp, json={"type": "DP"})
    assert r.status_code == 201
    order_id = r.json()["order_id"]
    from app.modules.payment.service import signature_for
    sig = signature_for(order_id, "200", str(float(r.json()["amount"])))
    
    r = await client.post("/payments/webhook", json={
        "order_id": order_id,
        "status_code": "200",
        "gross_amount": str(float(r.json()["amount"])),
        "signature_key": sig,
        "transaction_status": "settlement",
        "transaction_id": "trx1"
    })
    assert r.status_code == 200

    # 10. Rental confirms
    r = await client.post(f"/bookings/{booking_id}/confirm", headers=hr)
    assert r.status_code == 200

    # 11. PELUNASAN intent + simulate
    r = await client.post(f"/bookings/{booking_id}/payments", headers=hp, json={"type": "PELUNASAN"})
    order_id = r.json()["order_id"]
    sig = signature_for(order_id, "200", str(float(r.json()["amount"])))
    r = await client.post("/payments/webhook", json={
        "order_id": order_id,
        "status_code": "200",
        "gross_amount": str(float(r.json()["amount"])),
        "signature_key": sig,
        "transaction_status": "settlement",
        "transaction_id": "trx2"
    })
    assert r.status_code == 200

    # 12. Handover
    r = await client.post(f"/bookings/{booking_id}/handover", headers=hr, json={
        "odometer": 1000, "bbm_persen": 100
    })
    assert r.status_code == 200

    # 13. Return
    r = await client.post(f"/bookings/{booking_id}/return", headers=hr, json={
        "odometer": 1500, "bbm_persen": 50
    })
    assert r.status_code == 200

    # 14. Penyewa reviews
    r = await client.post(f"/bookings/{booking_id}/reviews", headers=hp, json={
        "rating": 5, "komentar": "Bagus"
    })
    assert r.status_code == 201

    # 15. Search same dates excludes nothing
    r = await client.get(f"/search?start_date={start}&end_date={end}")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 0

    # 16. Dashboard
    r = await client.get("/rentals/me/dashboard", headers=hr)
    assert r.status_code == 200
    assert r.json()["pendapatan_dicairkan"] == 1050000
