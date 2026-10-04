import uuid
from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name = Column(String, index=True)
    payload = Column(String)
    timestamp = Column(DateTime, default=func.now())
