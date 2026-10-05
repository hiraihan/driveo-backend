from app.core.ids import new_id
from sqlalchemy import Column, String, DateTime, func
from app.core.time import utcnow
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    event_name = Column(String, index=True)
    payload = Column(String)
    actor_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, default=utcnow)
