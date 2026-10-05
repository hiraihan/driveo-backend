from app.modules.user.models import User
from app.core.enums import UserRole
from app.modules.auth.security import hash_password, create_access_token
from app.modules.user.service import get_or_create_role
from app.core.ids import new_id

async def make_user(db, role: UserRole = UserRole.PENYEWA, email: str | None = None, is_active: bool = True) -> User:
    email = email or f"user_{new_id()}@example.com"
    r = await get_or_create_role(db, role)
    u = User(email=email, password_hash=hash_password("password"), role_id=r.id, is_active=is_active)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u

async def make_admin(db, email: str | None = None) -> User:
    return await make_user(db, role=UserRole.ADMIN, email=email)

def auth_header(user: User, role: UserRole | None = None) -> dict:
    token = create_access_token(user.id, role or UserRole.PENYEWA)
    return {"Authorization": f"Bearer {token}"}
