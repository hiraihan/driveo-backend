from datetime import datetime
from pydantic import Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import ListingStatus
from typing import Optional

class ListingCreate(RequestModel):
    vehicle_id: str
    judul: str
    deskripsi: str | None = None
    biaya_tambahan: int = Field(0, ge=0)

class ListingUpdate(RequestModel):
    judul: Optional[str] = None
    deskripsi: Optional[str] = None
    biaya_tambahan: Optional[int] = Field(None, ge=0)

class ListingResponse(ResponseModel):
    id: str
    vehicle_id: str
    rental_id: str
    judul: str
    deskripsi: str | None
    harga_all_in: int
    status_publikasi: ListingStatus
    updated_at: datetime
    is_stale: bool
