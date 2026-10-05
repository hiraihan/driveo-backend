from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.core.time import utcnow
from app.core.ids import new_id
from app.core.database import Base

class Rental(Base):
    __tablename__ = "rentals"
    id = Column(String(36), primary_key=True, default=new_id)
    nama_usaha = Column(String)
    nib = Column(String)
    alamat = Column(String)
    kontak = Column(String)
    status_verifikasi = Column(String, default="MENUNGGU")
    membership_id = Column(String(36), nullable=True)
    payout_account = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    is_active = Column(Boolean, default=True)

class RentalStaff(Base):
    __tablename__ = "rental_staff"
    id = Column(String(36), primary_key=True, default=new_id)
    rental_id = Column(String(36), ForeignKey("rentals.id", ondelete="RESTRICT"), index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), unique=True, index=True)
    is_owner = Column(Boolean, default=False)
