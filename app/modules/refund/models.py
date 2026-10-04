import uuid
from sqlalchemy import Column, String, DateTime, func, Float
from app.core.database import Base

class Refund(Base):
    __tablename__ = "refunds"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), index=True)
    amount = Column(Float)
    status = Column(String, default="DIPROSES")
    created_at = Column(DateTime, default=func.now())
