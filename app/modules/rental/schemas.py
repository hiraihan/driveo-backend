from pydantic import Field
from typing import Literal
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import RentalStatus

class OnboardRequest(RequestModel):
    nama_usaha: str
    nib: str
    alamat: str
    kontak: str
    payout_account: str

class RentalResponse(ResponseModel):
    id: str
    nama_usaha: str
    nib: str
    alamat: str
    kontak: str
    status_verifikasi: RentalStatus

class VerifyRequest(RequestModel):
    status: Literal[RentalStatus.LOLOS, RentalStatus.DITOLAK]
    alasan: str | None = None

from typing import Dict, List
from app.modules.booking.schemas import BookingResponse

class DashboardResponse(ResponseModel):
    total_bookings: int
    bookings_by_state: Dict[str, int]
    pendapatan_dicairkan: int
    escrow_ditahan: int
    upcoming_handovers: List[BookingResponse]
