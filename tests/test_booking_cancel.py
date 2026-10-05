import pytest
from app.modules.booking.service import cancel_booking, get_booking_for_actor
from app.core.enums import BookingState, EscrowState, UserRole
from app.core.errors import Forbidden, InvalidTransition
from app.modules.payment.escrow import hold, balance
import datetime
from sqlalchemy import select

async def test_cancel_other_users_booking_403(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    stranger = await make_user(db, email="s@s.com")
    rental_owner = await make_user(db, email="o@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing)
    
    from app.modules.auth.dependencies import CurrentUser
    from app.core.enums import UserRole
    with pytest.raises(Forbidden):
        await get_booking_for_actor(db, booking.id, CurrentUser(id=stranger.id, email=stranger.email, role=UserRole.PENYEWA))

async def test_cancel_selesai_409_slots_kept(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    from app.modules.availability.service import lock_slots
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o2@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.SELESAI)
    await lock_slots(db, vehicle.id, booking.tanggal_mulai, booking.tanggal_selesai, booking.id)
    await db.commit()
    
    with pytest.raises(InvalidTransition):
        await cancel_booking(db, booking, penyewa.id, "Bosan", False)

async def test_cancel_h0_after_dp_forfeits(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    from app.core.time import today_wib
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o3@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    booking.tanggal_mulai = today_wib()
    await hold(db, booking.id, booking.dp, "DP-REF")
    await db.commit()
    
    res = await cancel_booking(db, booking, penyewa.id, "Alasan", False)
    await db.commit()
    
    assert res.escrow_state == EscrowState.DICAIRKAN
    assert res.booking_state == BookingState.DIBATALKAN
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_cancel_h2_full_refund(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    from app.core.time import today_wib
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o4@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    booking.tanggal_mulai = today_wib() + datetime.timedelta(days=2)
    await hold(db, booking.id, booking.dp, "DP-REF")
    await db.commit()
    
    res = await cancel_booking(db, booking, penyewa.id, "Alasan", False)
    await db.commit()
    
    assert res.escrow_state == EscrowState.DIKEMBALIKAN
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_rental_cancel_always_full_refund(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    from app.core.time import today_wib
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o5@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    booking.tanggal_mulai = today_wib() # H-0
    await hold(db, booking.id, booking.dp, "DP-REF")
    await db.commit()
    
    # Rental cancels
    res = await cancel_booking(db, booking, rental_owner.id, "Kendaraan rusak", True)
    await db.commit()
    
    assert res.escrow_state == EscrowState.DIKEMBALIKAN
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_alasan_in_body(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o6@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_DP)
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/cancel?alasan=ignored", json={"alasan": "body reason"}, headers=auth_header(penyewa))
    assert res.status_code == 200
    assert res.json()["booking_state"] == BookingState.DIBATALKAN.value
    await db.refresh(booking)
    assert booking.alasan_batal == "body reason"

