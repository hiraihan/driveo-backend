from app.core.ids import new_id
from sqlalchemy import Column, String, DateTime, func, Boolean, ForeignKey
from app.core.time import utcnow
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role_id = Column(String(36))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    name = Column(String, unique=True)

class UserConsent(Base):
    __tablename__ = "user_consents"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    user_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    document_type = Column(String)
    version = Column(String)
    timestamp = Column(DateTime, default=utcnow)
