from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.booking.models import Booking
from app.modules.booking.schemas import BookingCreate, BookingResponse
from app.modules.booking.service import create_booking, get_booking
from app.modules.booking.state import transition
from app.core.enums import BookingEvent
from app.modules.auth.dependencies import get_current_user, CurrentUser
from app.modules.availability.service import release_slots

router = APIRouter()

@router.post("", status_code=201, response_model=BookingResponse)
async def create_booking_api(req: BookingCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await create_booking(db, current_user, req)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("", response_model=list[BookingResponse])
async def get_my_bookings(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.user_id == current_user.id))
    return result.scalars().all()

from pydantic import BaseModel

class CancelRequest(BaseModel):
    alasan: str

@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, req: CancelRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking(db, booking_id)
    transition(booking, BookingEvent.CANCEL)
    booking.alasan_batal = req.alasan
    booking.dibatalkan_oleh = current_user.id
    
    await release_slots(db, booking.id)
    await db.commit()
    return {"message": "Booking cancelled", "state": booking.booking_state}

from app.modules.payment.schemas import PaymentIntentRequest, PaymentIntentResponse
from app.modules.payment.service import create_payment_intent
from app.core.errors import Forbidden

@router.post("/{booking_id}/payments", status_code=201, response_model=PaymentIntentResponse)
async def create_payment(booking_id: str, req: PaymentIntentRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking(db, booking_id)
    if booking.user_id != current_user.id:
        raise Forbidden("Akses ditolak")
    
    payment = await create_payment_intent(db, booking, req.type)
    await db.commit()
    await db.refresh(payment)
    return PaymentIntentResponse(
        order_id=payment.order_id,
        amount=payment.amount,
        type=payment.type,
        status=payment.status,
        redirect_url=f"https://app.sandbox.midtrans.com/snap/v2/vtweb/{payment.order_id}"
    )
