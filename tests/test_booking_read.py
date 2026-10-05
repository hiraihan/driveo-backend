import pytest
from app.modules.booking.service import get_booking_for_actor
from app.core.errors import Forbidden
from app.core.enums import UserRole

async def test_get_booking_access(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, make_admin
    from app.modules.auth.dependencies import CurrentUser
    from app.core.enums import UserRole
    penyewa = await make_user(db)
    stranger = await make_user(db, email="s@s.com")
    rental_owner = await make_user(db, email="o@o.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing)
    admin = await make_admin(db)
    
    assert (await get_booking_for_actor(db, booking.id, CurrentUser(id=penyewa.id, email=penyewa.email, role=UserRole.PENYEWA))).id == booking.id
    assert (await get_booking_for_actor(db, booking.id, CurrentUser(id=rental_owner.id, email=rental_owner.email, role=UserRole.RENTAL))).id == booking.id
    assert (await get_booking_for_actor(db, booking.id, CurrentUser(id=admin.id, email=admin.email, role=UserRole.ADMIN))).id == booking.id
    
    with pytest.raises(Forbidden):
        await get_booking_for_actor(db, booking.id, CurrentUser(id=stranger.id, email=stranger.email, role=UserRole.PENYEWA))

