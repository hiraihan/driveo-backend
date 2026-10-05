import pytest
from app.modules.booking.service import expire_unpaid_bookings, breach_unconfirmed_bookings
from app.core.time import utcnow
from app.core.enums import BookingState
import datetime
import asyncio
from app.jobs import run_jobs_once, job_loop

async def test_expire_releases_slots(db):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_DP)
    # created_at < now - dp_expiry_minutes
    booking.created_at = utcnow() - datetime.timedelta(minutes=61)
    await db.commit()
    
    count = await expire_unpaid_bookings(db, utcnow())
    assert count == 1
    
    await db.refresh(booking)
    assert booking.booking_state == BookingState.DIBATALKAN

async def test_sla_breach_refunds(db):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    from app.modules.payment.escrow import hold, balance
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o2@j.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_KONFIRMASI_RENTAL)
    booking.dp_paid_at = utcnow() - datetime.timedelta(minutes=121)
    await hold(db, booking.id, booking.dp, "DP")
    await db.commit()
    
    count = await breach_unconfirmed_bookings(db, utcnow())
    assert count == 1
    
    await db.refresh(booking)
    assert booking.booking_state == BookingState.DIBATALKAN
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_job_failure_isolated(monkeypatch, db):
    # run_jobs_once should not crash if expire_unpaid_bookings raises
    async def mock_fail(*a, **kw):
        raise ValueError("Job crashed")
    import app.modules.booking.service as svc
    monkeypatch.setattr(svc, "expire_unpaid_bookings", mock_fail)
    
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    engine = db.bind
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    res = await run_jobs_once(async_session)
    assert "expire" in res
    assert res["expire"] == -1 # convention or just log
