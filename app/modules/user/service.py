from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.user.models import Role, User
from app.core.enums import UserRole

async def get_or_create_role(db: AsyncSession, role: UserRole) -> Role:
    result = await db.execute(select(Role).where(Role.name == role.value))
    r = result.scalars().first()
    if not r:
        from app.core.ids import new_id
        r = Role(id=new_id(), name=role.value)
        db.add(r)
        await db.commit()
        await db.refresh(r)
    return r

async def get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_user_role(db: AsyncSession, user: User) -> UserRole:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    r = result.scalars().first()
    if r:
        return UserRole(r.name)
    return UserRole.PENYEWA

async def set_user_role(db: AsyncSession, user_id: str, role: UserRole) -> None:
    u = await get_user(db, user_id)
    if u:
        r = await get_or_create_role(db, role)
        u.role_id = r.id
        await db.commit()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, email: str, password_hash: str, role: UserRole) -> User:
    from app.core.ids import new_id
    from app.core.errors import Conflict
    existing = await get_user_by_email(db, email)
    if existing:
        raise Conflict("EMAIL_TAKEN", "Email sudah digunakan")
    r = await get_or_create_role(db, role)
    u = User(id=new_id(), email=email, password_hash=password_hash, role_id=r.id)
    db.add(u)
    await db.flush()
    return u
