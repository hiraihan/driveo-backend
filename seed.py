import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.modules.user.models import User
from app.modules.user.service import get_or_create_role
from app.core.enums import UserRole
from app.modules.auth.security import hash_password
from app.core.ids import new_id

async def seed_data(session: AsyncSession) -> None:
    settings = get_settings()
    
    # Check if already seeded
    result = await session.execute(select(User).where(User.email == "admin@driveo.com"))
    if result.scalars().first():
        return
        
    print("Seeding database...")
    
    # Admin
    if settings.seed_admin_password:
        role_admin = await get_or_create_role(session, UserRole.ADMIN)
        admin = User(
            id=new_id(), 
            email="admin@driveo.com", 
            password_hash=hash_password(settings.seed_admin_password), 
            role_id=role_admin.id
        )
        session.add(admin)
        await session.commit()
    
    # Demo data
    if settings.env != "prod":
        # Additional demo data goes here
        # For now, just create roles
        await get_or_create_role(session, UserRole.RENTAL)
        await get_or_create_role(session, UserRole.PENYEWA)
        pass

if __name__ == "__main__":
    from app.core.database import async_session
    async def run():
        async with async_session() as session:
            await seed_data(session)
    asyncio.run(run())
