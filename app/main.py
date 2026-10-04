import sys
import os

import asyncio
from sqlalchemy.future import select
from datetime import datetime, timedelta
from app.modules.booking.models import Booking
from app.modules.admin.models import MembershipPlan, Promo
from app.modules.booking.state import process_cancellation

async def cancel_expired_bookings():
    while True:
        await asyncio.sleep(60) # Run every minute
        from app.core.database import async_session
        async with async_session() as session:
            # Check for MENUNGGU_DP older than 1 hour
            expire_limit = datetime.utcnow() - timedelta(hours=1)
            query = select(Booking).where(Booking.booking_state == "MENUNGGU_DP", Booking.created_at < expire_limit)
            result = await session.execute(query)
            expired = result.scalars().all()
            for b in expired:
                process_cancellation(b, "Batal Otomatis (Waktu Habis)")
                print(f"Auto-cancelled booking {b.id}")
            if expired:
                await session.commit()

from fastapi import FastAPI
from app.modules.auth.routers import router as auth_router

app = FastAPI(title="DriveO Backend")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
from app.modules.user.routers import router as user_router
from app.modules.rental.routers import router as rental_router
from app.modules.vehicle.routers import router as vehicle_router
from app.modules.availability.routers import router as availability_router
from app.modules.listing.routers import router as listing_router
from app.modules.search.routers import router as search_router
from app.modules.booking.routers import router as booking_router
from app.modules.payment.routers import router as payment_router
from app.modules.verification.routers import router as verification_router
from app.modules.review.routers import router as review_router
from app.modules.admin.routers import router as admin_router
from app.modules.notification.routers import router as notification_router
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(rental_router, prefix="/rentals", tags=["rentals"])
app.include_router(vehicle_router, prefix="/vehicles", tags=["vehicles"])
app.include_router(availability_router, prefix="/availability", tags=["availability"])
app.include_router(listing_router, prefix="/listings", tags=["listings"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(booking_router, prefix="/bookings", tags=["bookings"])
app.include_router(payment_router, prefix="/payments", tags=["payments"])
app.include_router(verification_router, prefix="/verifications", tags=["verifications"])
app.include_router(review_router, prefix="/reviews", tags=["reviews"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(notification_router, prefix="/notifications", tags=["notifications"])

from app.core.database import engine, Base
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(cancel_expired_bookings())
    try:
        from seed import seed_data
        await seed_data()
    except Exception as e:
        print('Seed error:', e)
