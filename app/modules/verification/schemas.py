from typing import Literal
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.core.schemas import ResponseModel, RequestModel
from app.core.enums import VerificationStatus

class VerificationResponse(ResponseModel):
    id: str
    status: str
    created_at: datetime
    alasan: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class ReviewRequest(RequestModel):
    status: Literal[VerificationStatus.TERVERIFIKASI, VerificationStatus.DITOLAK]
    alasan: str | None = None
