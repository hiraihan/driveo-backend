import uuid
from sqlalchemy import Column, String, DateTime, func, Boolean, Float, Integer
from app.core.database import Base

class Listing(Base):
    __tablename__ = "listings"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = Column(String(36), index=True)
    judul = Column(String)
    deskripsi = Column(String, nullable=True)
    harga_all_in = Column(Float)
    skor_kebasuan = Column(Integer, default=0)
    status_publikasi = Column(String, default="PUBLISHED")
