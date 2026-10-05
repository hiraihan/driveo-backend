from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.core.time import utcnow
from app.core.ids import new_id

class HandoverChecklist(Base):
    __tablename__ = "handover_checklists"
    id = Column(String(36), primary_key=True, default=new_id)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    tipe = Column(String, nullable=False) # HANDOVER or RETURN
    odometer = Column(Integer, nullable=False)
    bbm_persen = Column(Integer, nullable=False)
    catatan = Column(String, nullable=True)
    foto_urls = Column(JSONB, nullable=False, default=list)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    
    __table_args__ = (
        UniqueConstraint("booking_id", "tipe", name="uq_booking_tipe"),
    )
