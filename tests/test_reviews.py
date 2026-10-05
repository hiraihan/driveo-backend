import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import BookingState

async def test_review_requires_selesai(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="rev_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.BERJALAN)
    await db.commit()
    
    payload = {"rating": 5, "komentar": "Good"}
    res = await client.post(f"/bookings/{booking.id}/reviews", json=payload, headers=auth_header(penyewa))
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "BOOKING_NOT_COMPLETED"

async def test_rating_bounds(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="rev_owner2@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.SELESAI)
    await db.commit()
    
    res = await client.post(f"/bookings/{booking.id}/reviews", json={"rating": 0, "komentar": "Bad"}, headers=auth_header(penyewa))
    assert res.status_code == 422
    
    res2 = await client.post(f"/bookings/{booking.id}/reviews", json={"rating": 6, "komentar": "Great"}, headers=auth_header(penyewa))
    assert res2.status_code == 422

async def test_one_per_side(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="rev_owner3@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.SELESAI)
    await db.commit()
    
    payload = {"rating": 5, "komentar": "Awesome"}
    res = await client.post(f"/bookings/{booking.id}/reviews", json=payload, headers=auth_header(penyewa))
    assert res.status_code == 201
    
    res2 = await client.post(f"/bookings/{booking.id}/reviews", json=payload, headers=auth_header(penyewa))
    assert res2.status_code == 409
    
    res3 = await client.post(f"/bookings/{booking.id}/reviews", json=payload, headers=auth_header(rental_owner))
    assert res3.status_code == 201

async def test_stranger_403(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    stranger = await make_user(db, email="stranger@s.com")
    rental_owner = await make_user(db, email="rev_owner4@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.SELESAI)
    await db.commit()
    
    payload = {"rating": 5, "komentar": "Awesome"}
    res = await client.post(f"/bookings/{booking.id}/reviews", json=payload, headers=auth_header(stranger))
    assert res.status_code == 403

async def test_rental_average(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa1 = await make_user(db)
    penyewa2 = await make_user(db, email="p2@o.com")
    rental_owner = await make_user(db, email="rev_owner5@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    
    b1 = await make_booking(db, penyewa1, listing, state=BookingState.SELESAI)
    b2 = await make_booking(db, penyewa2, listing, state=BookingState.SELESAI)
    await db.commit()
    
    await client.post(f"/bookings/{b1.id}/reviews", json={"rating": 4, "komentar": "Good"}, headers=auth_header(penyewa1))
    await client.post(f"/bookings/{b2.id}/reviews", json={"rating": 5, "komentar": "Great"}, headers=auth_header(penyewa2))
    
    res = await client.get(f"/rentals/{rental.id}/reviews")
    assert res.status_code == 200
    data = res.json()
    assert data["average_rating"] == 4.5
    assert len(data["items"]["data"]) == 2
