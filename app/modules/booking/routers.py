from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.core.database import get_db
from app.modules.booking.models import Booking
from app.modules.vehicle.models import VehicleAvailability
from app.modules.booking.state import process_cancellation
from app.modules.auth.dependencies import get_current_user
from pydantic import BaseModel
from datetime import date, timedelta
from typing import List

router = APIRouter()

class BookingCreate(BaseModel):
    rental_id: str
    vehicle_id: str
    tanggal_mulai: date
    tanggal_selesai: date
    total_nilai: float
    dp: float
    sisa: float

@router.post("", status_code=201)
async def create_booking(req: BookingCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Pengecekan Ketersediaan Kalender (Atomic Slot Lock)
    query = select(VehicleAvailability).where(
        VehicleAvailability.vehicle_id == req.vehicle_id,
        VehicleAvailability.tanggal >= req.tanggal_mulai,
        VehicleAvailability.tanggal <= req.tanggal_selesai,
        VehicleAvailability.status != "tersedia"
    )
    result = await db.execute(query)
    conflicts = result.scalars().all()
    
    if conflicts:
        raise HTTPException(status_code=400, detail="Kendaraan tidak tersedia pada tanggal tersebut.")
        
    # Lock slot
    curr_date = req.tanggal_mulai
    while curr_date <= req.tanggal_selesai:
        avail = VehicleAvailability(vehicle_id=req.vehicle_id, tanggal=curr_date, status="dipesan")
        db.add(avail)
        curr_date += timedelta(days=1)
        
    booking = Booking(user_id=current_user["sub"], **req.dict())
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("")
async def get_my_bookings(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.user_id == current_user["sub"]))
    return result.scalars().all()

@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, alasan: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    process_cancellation(booking, alasan)
    
    # Release calendar
    q_avail = select(VehicleAvailability).where(
        VehicleAvailability.vehicle_id == booking.vehicle_id,
        VehicleAvailability.tanggal >= booking.tanggal_mulai,
        VehicleAvailability.tanggal <= booking.tanggal_selesai
    )
    avails = await db.execute(q_avail)
    for a in avails.scalars().all():
        a.status = "tersedia"
        
    await db.commit()
    return {"message": "Booking cancelled", "state": booking.booking_state}
