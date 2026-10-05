from sqlalchemy import Column, String, DateTime
from app.core.database import Base
from app.core.time import utcnow
from app.core.ids import new_id
from app.core.enums import VerificationStatus

class Verification(Base):
    __tablename__ = "verifications"
    id = Column(String(36), primary_key=True, default=new_id)
    user_id = Column(String(36), index=True)
    status = Column(String, default=VerificationStatus.MENUNGGU.value)
    ktp_path = Column(String)
    selfie_path = Column(String)
    alasan = Column(String, nullable=True)
    reviewer_id = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
