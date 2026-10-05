from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, ForeignKey
from app.core.database import Base
from app.core.ids import new_id
from app.core.time import utcnow
from app.core.enums import VehicleStatus

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String(36), primary_key=True, default=new_id)
    rental_id = Column(String(36), ForeignKey("rentals.id", ondelete="RESTRICT"), index=True)
    jenis = Column(String)
    merk = Column(String)
    tipe = Column(String)
    plat_nomor = Column(String, unique=True)
    tarif_dasar = Column(BigInteger)
    status = Column(String, default=VehicleStatus.AKTIF.value)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

