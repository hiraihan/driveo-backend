from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.admin.models import Promo
from app.core.errors import ValidationFailed

async def get_valid_promo(db: AsyncSession, code: str, today: date) -> Promo:
    result = await db.execute(select(Promo).where(Promo.code == code, Promo.is_active == True))
    promo = result.scalars().first()
    if not promo or promo.valid_until < today:
        raise ValidationFailed("PROMO_INVALID", "Kode promo tidak valid atau kedaluwarsa")
    return promo
