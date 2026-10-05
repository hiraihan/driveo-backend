from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import engine
from app.models import Base
from app.core.errors import register_error_handlers

from app.modules.auth.routers import router as auth_router
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

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.seed_on_startup:
        try:
            from seed import seed_data
            from app.core.database import async_session
            async with async_session() as session:
                await seed_data(session)
        except Exception as e:
            print('Seed error:', e)
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="DriveO Backend", lifespan=lifespan)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    register_error_handlers(app)
    
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    api_router.include_router(user_router, prefix="/users", tags=["users"])
    api_router.include_router(rental_router, prefix="/rentals", tags=["rentals"])
    api_router.include_router(vehicle_router, prefix="/vehicles", tags=["vehicles"])
    api_router.include_router(availability_router)
    api_router.include_router(listing_router, prefix="/listings", tags=["listings"])
    api_router.include_router(search_router, prefix="/search", tags=["search"])
    api_router.include_router(booking_router, prefix="/bookings", tags=["bookings"])
    api_router.include_router(payment_router, prefix="/payments", tags=["payments"])
    api_router.include_router(verification_router, prefix="/verifications", tags=["verifications"])
    api_router.include_router(review_router, prefix="/reviews", tags=["reviews"])
    api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
    api_router.include_router(notification_router, prefix="/notifications", tags=["notifications"])
    
    @api_router.get("/health")
    async def health():
        return {"status": "ok"}
        
    app.include_router(api_router)
    
    return app

app = create_app()
