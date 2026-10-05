from datetime import datetime, timedelta, timezone
from typing import Literal
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings
from app.core.enums import UserRole
from app.core.errors import Unauthorized

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)

def create_access_token(user_id: str, role: UserRole) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    to_encode = {"sub": user_id, "role": role.value, "type": "access", "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    to_encode = {"sub": user_id, "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            raise Unauthorized("INVALID_TOKEN", "Tipe token tidak valid")
        return payload
    except jwt.PyJWTError:
        raise Unauthorized("INVALID_TOKEN", "Token tidak valid atau sudah kedaluwarsa")
