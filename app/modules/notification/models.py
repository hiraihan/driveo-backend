import uuid
from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String) # EMAIL, PUSH, WHATSAPP
    recipient = Column(String)
    subject = Column(String, nullable=True)
    body = Column(String)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=func.now())
