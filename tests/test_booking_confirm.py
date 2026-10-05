import pytest
from app.core.enums import BookingState, EscrowState, UserRole
from app.modules.payment.escrow import hold, balance

async def test_confirm_by_staff(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="c_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/confirm", headers=auth_header(rental_owner))
    assert res.status_code == 200
    assert res.json()["booking_state"] == BookingState.TERKONFIRMASI.value

async def test_confirm_by_penyewa_403(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="c2_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/confirm", headers=auth_header(penyewa))
    assert res.status_code == 403

async def test_confirm_twice_409(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="c3_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/confirm", headers=auth_header(rental_owner))
    assert res.status_code == 409

async def test_reject_full_refund_and_release(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="c4_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    await hold(db, booking.id, booking.dp, "REF")
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/reject", json={"alasan": "Mobil rusak"}, headers=auth_header(rental_owner))
    assert res.status_code == 200
    assert res.json()["booking_state"] == BookingState.DITOLAK.value
    assert res.json()["escrow_state"] == EscrowState.DIKEMBALIKAN.value
    
    bal = await balance(db, booking.id)
    assert bal == 0

