from sqlalchemy import Column, String, Float, Integer, Date, Boolean, ForeignKey, BigInteger
from app.core.ids import new_id
from app.core.database import Base

class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    name = Column(String, unique=True, index=True) # Basic, Pro, Max
    price = Column(BigInteger, default=0)
    max_vehicles = Column(Integer, default=5)
    max_staff = Column(Integer, default=1)

class Promo(Base):
    __tablename__ = "promos"
    id = Column(String(36), primary_key=True, default=lambda: new_id())
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Float)
    max_discount_amount = Column(BigInteger)
    valid_until = Column(Date)
    is_active = Column(Boolean, default=True)
