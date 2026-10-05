from sqlalchemy import Column, String, DateTime, Integer, UniqueConstraint, ForeignKey
from app.core.database import Base
from app.core.time import utcnow
from app.core.ids import new_id

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String(36), primary_key=True, default=new_id)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="RESTRICT"), index=True, nullable=False)
    author_id = Column(String(36), index=True, nullable=False)
    author_role = Column(String, nullable=False)
    target_id = Column(String(36), index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    komentar = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    __table_args__ = (
        UniqueConstraint("booking_id", "author_role", name="uq_review_booking_role"),
    )
