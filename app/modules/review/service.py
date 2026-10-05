from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import Any
from app.modules.review.models import Review
from app.modules.review.schemas import ReviewCreate
from app.core.enums import BookingState
from app.core.errors import Conflict

async def create_review(db: AsyncSession, booking: Any, author_id: str, author_role: str, target_id: str, req: ReviewCreate) -> Review:
    if booking.booking_state != BookingState.SELESAI.value:
        raise Conflict("BOOKING_NOT_COMPLETED", "Booking belum selesai")
        
    review = Review(
        booking_id=booking.id,
        author_id=author_id,
        author_role=author_role,
        target_id=target_id,
        rating=req.rating,
        komentar=req.komentar
    )
    db.add(review)
    try:
        await db.flush()
    except IntegrityError:
        raise Conflict("REVIEW_EXISTS", "Review sudah ada")
        
    return review

async def get_rental_average_rating(db: AsyncSession, rental_id: str) -> float | None:
    stmt = select(func.avg(Review.rating)).where(Review.target_id == rental_id).where(Review.author_role == "Penyewa")
    result = await db.execute(stmt)
    avg = result.scalar()
    if avg is not None:
        return float(avg)
    return None
