import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import BookingState, EscrowState
from app.core.time import today_wib
import datetime

async def test_dashboard_numbers(db: AsyncSession, client: AsyncClient):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    from app.modules.payment.escrow import hold, release, refund
    
    penyewa = await make_user(db)
    stranger = await make_user(db, email="p2@o.com")
    rental_owner = await make_user(db, email="dash_owner@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    
    # 1. SELESAI booking, released 900000
    b1 = await make_booking(db, penyewa, listing, state=BookingState.SELESAI)
    b1.total_nilai = 900000
    b1.escrow_state = EscrowState.DICAIRKAN
    await hold(db, b1.id, 900000, "DP+SISA")
    await release(db, b1.id, "TRIP_COMPLETED")
    
    # 2. TERKONFIRMASI booking starting in 3 days, DP 270000 held
    today = today_wib()
    b2 = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    b2.tanggal_mulai = today + datetime.timedelta(days=3)
    b2.tanggal_selesai = today + datetime.timedelta(days=5)
    b2.dp = 270000
    b2.escrow_state = EscrowState.DITAHAN_ESCROW
    await hold(db, b2.id, 270000, "DP")
    
    # 3. DIBATALKAN
    b3 = await make_booking(db, penyewa, listing, state=BookingState.DIBATALKAN)
    b3.escrow_state = EscrowState.NONE
    
    await db.commit()
    
    # Access as staff
    res = await client.get("/rentals/me/dashboard", headers=auth_header(rental_owner))
    assert res.status_code == 200
    data = res.json()
    
    assert data["total_bookings"] == 3
    assert data["pendapatan_dicairkan"] == 900000
    assert data["escrow_ditahan"] == 270000
    assert data["bookings_by_state"]["SELESAI"] == 1
    assert data["bookings_by_state"]["TERKONFIRMASI"] == 1
    assert data["bookings_by_state"]["DIBATALKAN"] == 1
    
    assert len(data["upcoming_handovers"]) == 1
    assert data["upcoming_handovers"][0]["id"] == b2.id
    
    # Access as penyewa -> 403
    res_403 = await client.get("/rentals/me/dashboard", headers=auth_header(penyewa))
    assert res_403.status_code == 403

