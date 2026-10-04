from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.verification.models import Verification
from app.modules.auth.dependencies import get_current_user
import shutil
import os

router = APIRouter()

os.makedirs("uploads", exist_ok=True)

@router.post("/submit")
async def submit_verification(ktp: UploadFile = File(...), selfie: UploadFile = File(...), current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Mock saving to S3 by saving locally
    ktp_path = f"uploads/{current_user['sub']}_ktp_{ktp.filename}"
    with open(ktp_path, "wb") as buffer:
        shutil.copyfileobj(ktp.file, buffer)
        
    v = Verification(user_id=current_user["sub"], status="MENUNGGU", data_ektp=f"s3://driveo-bucket/{ktp_path}")
    db.add(v)
    await db.commit()
    return {"message": "Verification submitted successfully", "ktp_url": v.data_ektp, "ocr_result": {"nik": "3171234567890001", "nama": "Budi Santoso"}}
