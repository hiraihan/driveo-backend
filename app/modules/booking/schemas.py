from datetime import date, datetime
from typing import Literal
from pydantic import ConfigDict, Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import BookingState, EscrowState

class ChecklistRequest(RequestModel):
    odometer: int = Field(ge=0)
    bbm_persen: int = Field(ge=0, le=100)
    catatan: str | None = None
    foto_urls: list[str] = Field(default_factory=list)

class ChecklistResponse(ResponseModel):
    id: str
    booking_id: str
    tipe: str
    odometer: int
    bbm_persen: int
    catatan: str | None
    foto_urls: list[str]
    created_by: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

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
