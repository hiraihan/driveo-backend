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
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(rental_router, prefix="/rentals", tags=["rentals"])
app.include_router(vehicle_router, prefix="/vehicles", tags=["vehicles"])
app.include_router(availability_router, prefix="/availability", tags=["availability"])
app.include_router(listing_router, prefix="/listings", tags=["listings"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(booking_router, prefix="/bookings", tags=["bookings"])

from app.core.database import engine, Base
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
