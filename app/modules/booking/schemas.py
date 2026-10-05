from datetime import date, datetime
from typing import Literal
from pydantic import ConfigDict
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import BookingState, EscrowState

class BookingCreate(RequestModel):
    listing_id: str
    tanggal_mulai: date
    tanggal_selesai: date
    promo_code: str | None = None

class BookingResponse(ResponseModel):
    id: str
    user_id: str
    rental_id: str
    vehicle_id: str
    listing_id: str
    tanggal_mulai: date
    tanggal_selesai: date
    hari: int
    harga_per_hari: int
    subtotal: int
    diskon: int
    total_nilai: int
    dp: int
    sisa: int
    booking_state: BookingState
    escrow_state: EscrowState
    alasan_batal: str | None = None
    dibatalkan_oleh: str | None = None
    created_at: datetime
    updated_at: datetime
    dp_paid_at: datetime | None = None
    confirmed_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
