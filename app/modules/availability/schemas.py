from datetime import date
from pydantic import Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import SlotStatus

class BlockRequest(RequestModel):
    dates: list[date] = Field(min_length=1)

class SlotResponse(ResponseModel):
    tanggal: date
    status: SlotStatus
