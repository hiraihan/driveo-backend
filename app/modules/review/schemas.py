from datetime import datetime
from pydantic import Field, ConfigDict
from app.core.schemas import RequestModel, ResponseModel
from app.core.pagination import Page

class ReviewCreate(RequestModel):
    rating: int = Field(ge=1, le=5)
    komentar: str = Field(max_length=1000)

class ReviewResponse(ResponseModel):
    id: str
    booking_id: str
    author_id: str
    author_role: str
    target_id: str
    rating: int
    komentar: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class RentalReviewsResponse(ResponseModel):
    average_rating: float | None
    items: Page[ReviewResponse]
