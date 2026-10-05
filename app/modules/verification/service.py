from sqlalchemy.future import select
from sqlalchemy import desc
from app.core.enums import VerificationStatus
from app.contracts.ports import VerificationReadPort
from app.modules.verification.models import Verification

class VerificationService(VerificationReadPort):
    def __init__(self, db):
        self.db = db

    async def get_status(self, user_id: str) -> VerificationStatus:
        result = await self.db.execute(
            select(Verification)
            .where(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
        )
        v = result.scalars().first()
        if not v:
            return VerificationStatus.MENUNGGU
        return VerificationStatus(v.status)

async def get_verification(db, verification_id: str) -> Verification:
    result = await db.execute(select(Verification).where(Verification.id == verification_id))
    from app.core.errors import NotFound
    v = result.scalars().first()
    if not v:
        raise NotFound("Verifikasi tidak ditemukan")
    return v
