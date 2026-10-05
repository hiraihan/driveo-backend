from sqlalchemy import Column, String, Date, UniqueConstraint
from app.core.ids import new_id
from app.core.database import Base

class VehicleAvailability(Base):
    __tablename__ = "vehicle_availability"
    id = Column(String(36), primary_key=True, default=new_id)
    vehicle_id = Column(String(36), index=True)
    tanggal = Column(Date, index=True)
    status = Column(String) # dipesan / diblokir
    booking_id = Column(String(36), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("vehicle_id", "tanggal", name="uq_vehicle_tanggal"),
    )
