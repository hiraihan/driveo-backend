from datetime import date
from typing import Literal
from pydantic import BaseModel, model_validator
from app.core.errors import ValidationFailed

class SearchParams(BaseModel):
    q: str | None = None
    lokasi: str | None = None
    jenis: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort: Literal["freshness", "price_asc", "price_desc"] = "freshness"
    page: int = 1
    page_size: int = 10

    @model_validator(mode='after')
    def validate_dates(self) -> 'SearchParams':
        if (self.start_date and not self.end_date) or (not self.start_date and self.end_date):
            raise ValidationFailed("DATE_RANGE_INCOMPLETE", "Start date dan end date harus diisi keduanya atau tidak sama sekali")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationFailed("DATE_RANGE_INVALID", "End date tidak boleh lebih kecil dari start date")
        return self
