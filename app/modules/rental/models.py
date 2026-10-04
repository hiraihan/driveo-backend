import uuid
from sqlalchemy import Column, String, DateTime, func, Boolean
from app.core.database import Base

class Rental(Base):
    __tablename__ = "rentals"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nama_usaha = Column(String)
    nib = Column(String)
    alamat = Column(String)
    kontak = Column(String)
    status_verifikasi = Column(String, default="MENUNGGU")
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

class RentalPayoutAccount(Base):
    __tablename__ = "rental_payout_accounts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rental_id = Column(String(36), index=True)
    encrypted_account_info = Column(String) # Encrypted for SEC

class RentalStaff(Base):
    __tablename__ = "rental_staff"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rental_id = Column(String(36), index=True)
    user_id = Column(String(36), index=True)
    role = Column(String) # Admin/Staff
