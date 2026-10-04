from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.notification.models import Notification

router = APIRouter()

@router.get("/inbox/{recipient}")
async def get_mock_inbox(recipient: str, db: AsyncSession = Depends(get_db)):
    # LOMBA STANDARD: Let judges see what emails/SMS were 'sent' without a real SMTP
    result = await db.execute(select(Notification).where(Notification.recipient == recipient))
    return result.scalars().all()
