import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select
import uuid
from datetime import date
from app.modules.booking.models import Booking

async def test_booking_cancel():
    from app.core.database import async_session
    from app.modules.booking.state import process_cancellation
    
    async with async_session() as session:
        b = Booking(
            user_id="user1", 
            rental_id="rental1", 
            tanggal_mulai=date(2026, 12, 1), 
            tanggal_selesai=date(2026, 12, 3), 
            total_nilai=1500000, 
            dp=450000, 
            sisa=1050000,
            booking_state="MENUNGGU_DP"
        )
        session.add(b)
        await session.commit()
        
        process_cancellation(b, "Oleh penyewa")
        assert b.booking_state == "DIBATALKAN"
