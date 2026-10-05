from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.review.models import Review
from app.modules.review.schemas import ReviewCreate, ReviewResponse, RentalReviewsResponse
from app.modules.review.service import create_review, get_rental_average_rating
from app.modules.auth.dependencies import get_current_user, CurrentUser
from app.modules.booking.service import get_booking_for_actor
from app.modules.rental.service import get_rental_id_for_staff
from app.core.pagination import PageParams, paginate
from app.core.errors import Forbidden

router = APIRouter()

@router.post("/bookings/{booking_id}/reviews", status_code=201, response_model=ReviewResponse)
async def create_booking_review(booking_id: str, req: ReviewCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    booking = await get_booking_for_actor(db, booking_id, current_user)
    
    # Determine role and target
    if booking.user_id == current_user.id:
        author_role = "Penyewa"
        target_id = booking.rental_id
    else:
        staff_rental_id = await get_rental_id_for_staff(db, current_user.id)
        if not staff_rental_id or booking.rental_id != staff_rental_id:
            raise Forbidden("Akses ditolak")
        author_role = "Rental"
        target_id = booking.user_id
        
    review = await create_review(db, booking, current_user.id, author_role, target_id, req)
    await db.commit()
    await db.refresh(review)
    return review

@router.get("/rentals/{rental_id}/reviews", response_model=RentalReviewsResponse)
async def get_rental_reviews(rental_id: str, params: PageParams = Depends(), db: AsyncSession = Depends(get_db)):
    avg_rating = await get_rental_average_rating(db, rental_id)
    
    stmt = select(Review).where(Review.target_id == rental_id).where(Review.author_role == "Penyewa")
    page = await paginate(db, stmt, params, ReviewResponse)
    
    return RentalReviewsResponse(
        average_rating=avg_rating,
        items=page
    )
