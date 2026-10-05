import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import BookingState, EscrowState

async def test_handover_blocked_until_lunas(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o_hando@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    booking.escrow_state = EscrowState.DITAHAN_ESCROW
    await db.commit()
    
    payload = {"odometer": 1000, "bbm_persen": 50, "catatan": "OK", "foto_urls": []}
    res = await client.post(f"/bookings/{booking.id}/handover", json=payload, headers=auth_header(rental_owner))
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ESCROW_NOT_LUNAS"

async def test_handover_after_pelunasan(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o2_hando@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    booking.escrow_state = EscrowState.LUNAS
    await db.commit()
    
    payload = {"odometer": 1000, "bbm_persen": 50, "catatan": "OK", "foto_urls": []}
    res = await client.post(f"/bookings/{booking.id}/handover", json=payload, headers=auth_header(rental_owner))
    assert res.status_code == 200
    data = res.json()
    assert data["booking_state"] == BookingState.BERJALAN.value

async def test_return_completes_and_releases(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    from app.modules.payment.escrow import hold, balance
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o3_hando@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.BERJALAN)
    booking.escrow_state = EscrowState.LUNAS
    await hold(db, booking.id, booking.dp, "DP")
    await hold(db, booking.id, booking.sisa, "SISA")
    await db.commit()
    
    payload = {"odometer": 1100, "bbm_persen": 40, "catatan": "Good", "foto_urls": []}
    res = await client.post(f"/bookings/{booking.id}/return", json=payload, headers=auth_header(rental_owner))
    assert res.status_code == 200
    data = res.json()
    assert data["booking_state"] == BookingState.SELESAI.value
    assert data["escrow_state"] == EscrowState.DICAIRKAN.value
    
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_duplicate_handover_409(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o4_hando@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    booking.escrow_state = EscrowState.LUNAS
    await db.commit()
    
    payload = {"odometer": 1000, "bbm_persen": 50, "catatan": "OK", "foto_urls": []}
    res = await client.post(f"/bookings/{booking.id}/handover", json=payload, headers=auth_header(rental_owner))
    assert res.status_code == 200
    
    # Try again
    res2 = await client.post(f"/bookings/{booking.id}/handover", json=payload, headers=auth_header(rental_owner))
    assert res2.status_code == 409

async def test_bbm_out_of_range_422(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o5_hando@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    booking.escrow_state = EscrowState.LUNAS
    await db.commit()
    
    payload = {"odometer": 1000, "bbm_persen": 150, "catatan": "OK", "foto_urls": []}
    res = await client.post(f"/bookings/{booking.id}/handover", json=payload, headers=auth_header(rental_owner))
    assert res.status_code == 422
