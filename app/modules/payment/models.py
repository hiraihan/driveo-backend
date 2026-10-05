import uuid
from sqlalchemy import Column, String, DateTime, func, BigInteger, Enum
from app.core.database import Base
from app.core.enums import PaymentType, PaymentStatus, LedgerEntryType
from app.core.ids import new_id
from app.core.time import utcnow

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=new_id)
    booking_id = Column(String(36), index=True)
    type = Column(Enum(PaymentType, native_enum=False), nullable=False)
    order_id = Column(String, unique=True, nullable=False)
    amount = Column(BigInteger, nullable=False)
    status = Column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING)
    transaction_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)

class EscrowLedger(Base):
    __tablename__ = "escrow_ledgers"
    id = Column(String(36), primary_key=True, default=new_id)
    booking_id = Column(String(36), index=True)
    entry_type = Column(Enum(LedgerEntryType, native_enum=False), nullable=False)
    amount = Column(BigInteger, nullable=False)
    reference = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
