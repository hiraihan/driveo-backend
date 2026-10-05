import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import app.models  # noqa
from app.core.database import Base
from app.modules.booking.models import Booking
from app.core.ids import new_id

FK_COLUMNS = {
    ("bookings", "user_id"),
    ("bookings", "listing_id"),
    ("vehicles", "rental_id"),
    ("listings", "vehicle_id"),
    ("payments", "booking_id"),
    ("escrow_ledgers", "booking_id"),
    ("vehicle_availability", "vehicle_id"),
    ("rental_staff", "user_id"),
    ("reviews", "booking_id")
}

def test_foreign_keys_declared():
    for table, col in FK_COLUMNS:
        assert Base.metadata.tables[table].c[col].foreign_keys, f"{table}.{col} lacks FK"

async def test_orphan_booking_rejected(db: AsyncSession):
    import datetime
    booking = Booking(
        id=new_id(),
        user_id=new_id(),
        rental_id=new_id(),
        vehicle_id=new_id(),
        listing_id=new_id(),
        tanggal_mulai=datetime.date.today(),
        tanggal_selesai=datetime.date.today(),
        hari=1,
        harga_per_hari=100000,
        subtotal=100000,
        diskon=0,
        total_nilai=100000,
        dp=50000,
        sisa=50000
    )
    db.add(booking)
    with pytest.raises(IntegrityError):
        await db.commit()
