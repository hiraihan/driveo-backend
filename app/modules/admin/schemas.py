from datetime import date
from pydantic import Field
from app.core.schemas import RequestModel, ResponseModel

class PromoCreate(RequestModel):
    code: str = Field(pattern=r"^[A-Z0-9]{3,20}$")
    discount_percent: float = Field(gt=0, le=100)
    max_discount_amount: int = Field(gt=0)
    valid_until: date

class PromoResponse(ResponseModel):
    id: str
    code: str
    discount_percent: float
    max_discount_amount: int
    valid_until: date
    is_active: bool

class MembershipCreate(RequestModel):
    name: str
    price: int = Field(ge=0)
    max_vehicles: int = Field(ge=1)
    max_staff: int = Field(ge=1)

class MembershipResponse(ResponseModel):
    id: str
    name: str
    price: int
    max_vehicles: int
    max_staff: int
