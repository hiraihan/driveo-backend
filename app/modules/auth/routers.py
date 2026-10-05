from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.errors import Conflict, Unauthorized
from app.core.enums import UserRole
from app.modules.user.service import get_or_create_role, get_user_by_email, create_user, get_user_role
from app.modules.auth.schemas import RegisterRequest, UserResponse, TokenResponse, RefreshRequest
from app.modules.auth.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.ids import new_id

router = APIRouter()

@router.post("/register", status_code=201, response_model=UserResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, req.email, hash_password(req.password), UserRole.PENYEWA)
    if req.name:
        user.name = req.name
    if req.phone:
        user.phone = req.phone
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=user.id, email=user.email, role=UserRole.PENYEWA.value,
                        name=user.name, phone=user.phone)

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise Unauthorized("INVALID_CREDENTIALS", "Email atau password salah")
    
    role = await get_user_role(db, user)
    
    return TokenResponse(
        access_token=create_access_token(user.id, role),
        refresh_token=create_refresh_token(user.id)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token, "refresh")
    user_id = payload.get("sub")
    
    from app.modules.user.service import get_user, get_user_role
    user = await get_user(db, user_id)
    if not user or not user.is_active:
        raise Unauthorized("INVALID_TOKEN", "Pengguna tidak aktif")
        
    role = await get_user_role(db, user)
    return TokenResponse(
        access_token=create_access_token(user.id, role),
        refresh_token=create_refresh_token(user.id)
    )
