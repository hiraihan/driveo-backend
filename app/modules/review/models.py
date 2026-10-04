import uuid
from sqlalchemy import Column, String, DateTime, func, Integer
from app.core.database import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), index=True)
    user_id = Column(String(36), index=True)
    rental_id = Column(String(36), index=True)
    rating = Column(Integer)
    komentar = Column(String)
    created_at = Column(DateTime, default=func.now())
