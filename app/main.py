from fastapi import FastAPI
from app.modules.auth.routers import router as auth_router

app = FastAPI(title="DriveO Backend")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
from app.modules.user.routers import router as user_router
from app.modules.rental.routers import router as rental_router
app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(rental_router, prefix="/rentals", tags=["rentals"])
