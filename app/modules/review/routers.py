from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.review.models import Review
from app.modules.auth.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ReviewCreate(BaseModel):
    booking_id: str
    rental_id: str
    rating: int
    komentar: str

@router.post("")
async def create_review(req: ReviewCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    review = Review(user_id=current_user["sub"], **req.dict())
    db.add(review)
    await db.commit()
    return {"message": "Review added"}
