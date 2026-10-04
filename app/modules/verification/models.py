import uuid
from sqlalchemy import Column, String, DateTime, func
from app.core.database import Base

class Verification(Base):
    __tablename__ = "verifications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True)
    status = Column(String, default="MENUNGGU")
    data_ektp = Column(String)
    created_at = Column(DateTime, default=func.now())
