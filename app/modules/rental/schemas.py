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
