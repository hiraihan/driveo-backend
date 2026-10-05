from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.booking.models import Booking
from app.modules.booking.schemas import BookingCreate, BookingResponse
from app.modules.booking.service import (
    create_booking, 
    get_booking_for_actor, 
    cancel_booking as svc_cancel_booking,
    confirm_booking,
    reject_booking
)
from app.modules.auth.dependencies import get_current_user, CurrentUser
from app.core.pagination import PageParams, paginate, Page
from pydantic import BaseModel

from app.modules.payment.schemas import PaymentIntentRequest, PaymentIntentResponse
from app.modules.payment.service import create_payment_intent
from app.core.errors import Forbidden
from app.modules.rental.service import get_rental_id_for_staff

router = APIRouter()

@router.post("", status_code=201, response_model=BookingResponse)
async def create_booking_api(req: BookingCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await create_booking(db, current_user, req)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("", response_model=Page[BookingResponse])
async def get_my_bookings(
    state: Optional[str] = None,
    params: PageParams = Depends(),
    current_user: CurrentUser = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).where(Booking.user_id == current_user.id)
    if state:
        stmt = stmt.where(Booking.booking_state == state)
    return await paginate(db, stmt, params, BookingResponse)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id(booking_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_booking_for_actor(db, booking_id, current_user)

class CancelRequest(BaseModel):
    alasan: Optional[str] = None

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking_endpoint(booking_id: str, req: CancelRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking_for_actor(db, booking_id, current_user)
    # determine if cancelled by rental
    by_rental = False
    if booking.user_id != current_user.id:
        staff_rental_id = await get_rental_id_for_staff(db, current_user.id)
        if staff_rental_id and booking.rental_id == staff_rental_id:
            by_rental = True
            
    booking = await svc_cancel_booking(db, booking, current_user.id, req.alasan, by_rental)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.post("/{booking_id}/payments", status_code=201, response_model=PaymentIntentResponse)
async def create_payment(booking_id: str, req: PaymentIntentRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking_for_actor(db, booking_id, current_user)
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

class RejectRequest(BaseModel):
    alasan: str

@router.post("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking_endpoint(booking_id: str, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking_for_actor(db, booking_id, current_user)
    
    # Must be a staff member of the rental
    staff_rental_id = await get_rental_id_for_staff(db, current_user.id)
    if not staff_rental_id or booking.rental_id != staff_rental_id:
        raise Forbidden("Akses ditolak")

    booking = await confirm_booking(db, booking, current_user.id)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.post("/{booking_id}/reject", response_model=BookingResponse)
async def reject_booking_endpoint(booking_id: str, req: RejectRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking_for_actor(db, booking_id, current_user)
    
    # Must be a staff member of the rental
    staff_rental_id = await get_rental_id_for_staff(db, current_user.id)
    if not staff_rental_id or booking.rental_id != staff_rental_id:
        raise Forbidden("Akses ditolak")

    booking = await reject_booking(db, booking, current_user.id, req.alasan)
    await db.commit()
    await db.refresh(booking)
    return booking
