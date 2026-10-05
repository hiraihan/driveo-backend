import os
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.config import get_settings
from app.core.ids import new_id
from app.core.errors import AppError, Conflict
from app.core.enums import UserRole, VerificationStatus
from app.modules.verification.models import Verification
from app.modules.verification.schemas import VerificationResponse, ReviewRequest
from app.modules.verification.service import VerificationService, get_verification
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.modules.audit.service import AuditService
from app.modules.notification.service import NotificationService
from app.core.pagination import PageParams, Page, paginate
from app.modules.user.service import get_user

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

async def _save_file(upload_file: UploadFile, directory: str, filename: str, max_size: int) -> str:
    if upload_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError(code="UNSUPPORTED_MEDIA_TYPE", message="Tipe file tidak didukung", status_code=415)
        
    content = await upload_file.read()
    if len(content) > max_size:
        raise AppError(code="FILE_TOO_LARGE", message="Ukuran file melebihi batas", status_code=413)
        
    os.makedirs(directory, exist_ok=True)
    ext = "jpg" if upload_file.content_type == "image/jpeg" else "png"
    safe_name = f"{filename}.{ext}"
    path = os.path.join(directory, safe_name)
    
    def _write():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            
    await asyncio.to_thread(_write)
    return path

@router.post("", status_code=201, response_model=VerificationResponse)
async def submit_verification(
    ktp: UploadFile = File(...),
    selfie: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Verification)
        .where(Verification.user_id == current_user.id)
        .order_by(Verification.created_at.desc())
    )
    existing = result.scalars().first()
    
    if existing and existing.status in {VerificationStatus.MENUNGGU, VerificationStatus.TERVERIFIKASI}:
        raise Conflict("VERIFICATION_EXISTS", "Verifikasi sudah diajukan atau terverifikasi")
        
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, "verifications")
    
    ktp_path = await _save_file(ktp, upload_dir, new_id(), settings.max_upload_bytes)
    selfie_path = await _save_file(selfie, upload_dir, new_id(), settings.max_upload_bytes)
    
    v = Verification(
        user_id=current_user.id,
        status=VerificationStatus.MENUNGGU.value,
        ktp_path=ktp_path,
        selfie_path=selfie_path
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    
    return v

@router.get("/me", response_model=VerificationResponse)
async def get_my_verification(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Verification)
        .where(Verification.user_id == current_user.id)
        .order_by(Verification.created_at.desc())
    )
    v = result.scalars().first()
    if not v:
        from app.core.errors import NotFound
        raise NotFound("Verifikasi tidak ditemukan")
    return v

@router.get("", response_model=Page[VerificationResponse])
async def list_verifications(
    status: str | None = None,
    params: PageParams = Depends(),
    user: CurrentUser = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    query = select(Verification)
    if status:
        query = query.where(Verification.status == status)
    query = query.order_by(Verification.created_at.desc())
    return await paginate(db, query, params, VerificationResponse)

@router.post("/{id}/review")
async def review_verification(
    id: str,
    req: ReviewRequest,
    user: CurrentUser = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    v = await get_verification(db, id)
    if v.status != VerificationStatus.MENUNGGU.value:
        raise Conflict("VERIFICATION_ALREADY_REVIEWED", "Verifikasi sudah direview")
        
    v.status = req.status
    v.alasan = req.alasan
    v.reviewer_id = user.id
    from app.core.time import utcnow
    v.reviewed_at = utcnow()
    
    target_user = await get_user(db, v.user_id)
    email = target_user.email if target_user else v.user_id
    
    await AuditService(db).log_event("VERIFICATION_REVIEWED", {"verification_id": id, "status": req.status}, actor_id=user.id)
    await NotificationService(db).send(email, f"Verifikasi Anda {req.status}")
    
    await db.commit()
    await db.refresh(v)
    return {"message": "Review berhasil disimpan"}
