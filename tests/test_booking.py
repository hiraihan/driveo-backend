from app.modules.booking.models import Booking
import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select
import uuid
from datetime import date

async def test_booking_state_machine(client):
    from app.core.database import async_session
    from app.modules.booking.models import Booking
    
    async with async_session() as session:
        b = Booking(
            user_id="user1", 
            rental_id="rental1", 
            tanggal_mulai=date(2026, 12, 1), 
            tanggal_selesai=date(2026, 12, 3), 
            total_nilai=1500000, 
            dp=450000, 
            sisa=1050000
        )
        session.add(b)
        await session.commit()
        
        # Test initial state
        result = await session.execute(select(Booking).where(Booking.id == b.id))
        booking = result.scalars().first()
        assert booking.booking_state == "MENUNGGU_DP"
        
        # Test transitions (simulate webhook)
        from app.modules.booking.state import process_payment_success
        process_payment_success(booking)
        assert booking.booking_state == "MENUNGGU_KONFIRMASI_RENTAL"
