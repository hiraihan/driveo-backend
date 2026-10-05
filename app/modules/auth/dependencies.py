from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.enums import UserRole
from app.core.errors import Unauthorized, Forbidden
from app.modules.auth.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class CurrentUser(BaseModel):
    id: str
    email: str
    role: UserRole

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> CurrentUser:
    payload = decode_token(token, "access")
    user_id = payload.get("sub")
    
    from app.modules.user.service import get_user, get_user_role
    user = await get_user(db, user_id)
    if not user or not user.is_active:
        raise Unauthorized("INVALID_TOKEN", "Pengguna tidak aktif")
        
    role = await get_user_role(db, user)
    return CurrentUser(id=user.id, email=user.email, role=role)

def require_roles(*roles: UserRole):
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if roles and current_user.role not in roles:
            raise Forbidden("Akses ditolak: peran tidak memadai")
        return current_user
    return role_checker
