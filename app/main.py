from fastapi import FastAPI
from app.modules.auth.routers import router as auth_router

app = FastAPI(title="DriveO Backend")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
