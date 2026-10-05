from sqlalchemy import Column, String, DateTime, BigInteger, Boolean, ForeignKey
from app.core.database import Base
from app.core.ids import new_id
from app.core.time import utcnow
from app.core.enums import ListingStatus

class Listing(Base):
    __tablename__ = "listings"
    id = Column(String(36), primary_key=True, default=new_id)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True)
    rental_id = Column(String(36), ForeignKey("rentals.id", ondelete="RESTRICT"), index=True)
    judul = Column(String)
    deskripsi = Column(String, nullable=True)
    biaya_tambahan = Column(BigInteger, default=0)
    harga_all_in = Column(BigInteger, default=0)
    status_publikasi = Column(String, default=ListingStatus.DRAFT.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
