from pydantic import Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import VehicleStatus
from typing import Optional

class VehicleCreate(RequestModel):
    jenis: str
    merk: str
    tipe: str
    plat_nomor: str
    tarif_dasar: int = Field(gt=0)

class VehicleUpdate(RequestModel):
    jenis: Optional[str] = None
    merk: Optional[str] = None
    tipe: Optional[str] = None
    plat_nomor: Optional[str] = None
    tarif_dasar: Optional[int] = Field(None, gt=0)
    status: Optional[VehicleStatus] = None

class VehicleResponse(ResponseModel):
    id: str
    rental_id: str
    jenis: str
    merk: str
    tipe: str
    plat_nomor: str
    tarif_dasar: int
    status: VehicleStatus
