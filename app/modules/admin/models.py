import uuid
from sqlalchemy import Column, String, Float, Integer, Date, Boolean, ForeignKey
from app.core.database import Base

class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True) # Basic, Pro, Max
    price = Column(Float, default=0.0)
    max_vehicles = Column(Integer, default=5)
    max_staff = Column(Integer, default=1)

class Promo(Base):
    __tablename__ = "promos"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Float)
    max_discount_amount = Column(Float)
    valid_until = Column(Date)
    is_active = Column(Boolean, default=True)
