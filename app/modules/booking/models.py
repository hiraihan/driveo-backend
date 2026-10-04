import uuid
from sqlalchemy import Column, String, DateTime, func, Boolean, Float, Date
from app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True)
    rental_id = Column(String(36), index=True)
    vehicle_id = Column(String(36), index=True)
    tanggal_mulai = Column(Date)
    tanggal_selesai = Column(Date)
    booking_state = Column(String, default="MENUNGGU_DP")
    escrow_state = Column(String, default="NONE")
    total_nilai = Column(Float)
    dp = Column(Float)
    sisa = Column(Float)
    created_at = Column(DateTime, default=func.now())
