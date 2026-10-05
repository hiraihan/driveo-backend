from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.payment.schemas import MidtransNotification
from app.modules.payment.service import handle_notification

router = APIRouter()

@router.post("/webhook")
async def payment_webhook(payload: MidtransNotification, db: AsyncSession = Depends(get_db)):
    payment = await handle_notification(db, payload)
    await db.commit()
    return {"message": "Webhook processed", "status": payment.status}
