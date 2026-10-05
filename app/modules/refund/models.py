from sqlalchemy import Column, String, DateTime, func, BigInteger, ForeignKey
from app.core.database import Base
from app.core.ids import new_id
from app.core.time import utcnow

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(String(36), primary_key=True, default=new_id)
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="RESTRICT"), index=True)
    amount = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="DIPROSES")
    created_at = Column(DateTime(timezone=True), default=utcnow)
