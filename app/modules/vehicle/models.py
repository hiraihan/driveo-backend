import uuid
from sqlalchemy import Column, String, DateTime, func, Boolean, Float, Date
from app.core.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rental_id = Column(String(36), index=True)
    jenis = Column(String)
    merk = Column(String)
    tipe = Column(String)
    plat_nomor = Column(String)
    tarif_dasar = Column(Float)
    status = Column(String, default="aktif")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class VehicleAvailability(Base):
    __tablename__ = "vehicle_availability"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = Column(String(36), index=True)
    tanggal = Column(Date, index=True)
    status = Column(String) # tersedia/dipesan/diblokir manual
