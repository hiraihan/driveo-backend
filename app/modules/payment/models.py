import uuid
from sqlalchemy import Column, String, DateTime, func, Float
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), index=True)
    amount = Column(Float)
    status = Column(String, default="PENDING")
    external_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

class EscrowLedger(Base):
    __tablename__ = "escrow_ledgers"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), index=True)
    amount = Column(Float)
    status = Column(String, default="DITAHAN") # DITAHAN, DICAIRKAN, DIKEMBALIKAN
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
