from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.payment.models import Payment, EscrowLedger
from app.modules.booking.models import Booking
from app.modules.booking.state import transition
from app.core.enums import BookingEvent
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
            transition(booking, BookingEvent.DP_PAID)
            booking.escrow_state = "DITAHAN_ESCROW"
            
            # Put into Escrow
            escrow = EscrowLedger(booking_id=booking.id, amount=payload.amount, status="DITAHAN")
            db.add(escrow)
            
    await db.commit()
    return {"message": "Webhook processed"}


@router.post("/simulate")
async def simulate_payment(booking_id: str, db: AsyncSession = Depends(get_db)):
    # LOMBA STANDARD: Helper endpoint for Frontend to quickly mock a successful Midtrans Payment
    b_result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = b_result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    payload = WebhookPayload(
        booking_id=booking_id,
        amount=booking.sisa,
        status="BERHASIL",
        external_id="mock_midtrans_999"
    )
    return await payment_webhook(payload, db)
