from sqlalchemy import Column, String, DateTime, Date, BigInteger, Integer, ForeignKey
from app.core.database import Base
from app.core.time import utcnow
from app.core.ids import new_id
from app.core.enums import BookingState, EscrowState

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    rental_id = Column(String(36), ForeignKey("rentals.id", ondelete="RESTRICT"), index=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True)
    listing_id = Column(String(36), ForeignKey("listings.id", ondelete="RESTRICT"), index=True)
    tanggal_mulai = Column(Date)
    tanggal_selesai = Column(Date)
    
    hari = Column(Integer)
    harga_per_hari = Column(BigInteger)
    subtotal = Column(BigInteger)
    diskon = Column(BigInteger)
    promo_id = Column(String(36), ForeignKey("promos.id", ondelete="RESTRICT"), nullable=True)
    total_nilai = Column(BigInteger)
    dp = Column(BigInteger)
    sisa = Column(BigInteger)
    
    booking_state = Column(String, default=BookingState.MENUNGGU_DP.value)
    escrow_state = Column(String, default=EscrowState.NONE.value)
    
    alasan_batal = Column(String, nullable=True)
    dibatalkan_oleh = Column(String(36), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    dp_paid_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
