from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.payment.models import Payment, EscrowLedger
from app.modules.booking.models import Booking
from app.modules.booking.state import process_payment_success
from pydantic import BaseModel

router = APIRouter()

class WebhookPayload(BaseModel):
    booking_id: str
    amount: float
    status: str
    external_id: str

@router.post("/webhook")
async def payment_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    # Simulates receiving webhook from Midtrans
    payment = Payment(**payload.dict())
    db.add(payment)
    
    if payload.status == "BERHASIL":
        # Process booking state
        b_result = await db.execute(select(Booking).where(Booking.id == payload.booking_id))
        booking = b_result.scalars().first()
        if booking:
            process_payment_success(booking)
            
            # Put into Escrow
            escrow = EscrowLedger(booking_id=booking.id, amount=payload.amount, status="DITAHAN")
            db.add(escrow)
            
    await db.commit()
    return {"message": "Webhook processed"}
