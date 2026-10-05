"""Marketplace module - public catalog mirroring the frontend domain.

These tables mirror the frontend `types/domain.ts` shapes directly so the
frontend can consume seeded dummy data via the API without reshaping.
"""
from sqlalchemy import Column, String, DateTime, Boolean, BigInteger, Integer, Float, JSON
from app.core.database import Base
from app.core.ids import new_id
from app.core.time import utcnow


class PickupSpot(Base):
    __tablename__ = "pickup_spots"
    id = Column(String(36), primary_key=True)
    name = Column(String)
    code = Column(String)
    area = Column(String)
    description = Column(String)
    extra_fee = Column(BigInteger, default=0)
    is_popular = Column(Boolean, default=False)
    estimated_delivery_min = Column(Integer, default=0)


class MarketplaceRental(Base):
    __tablename__ = "marketplace_rentals"
    id = Column(String(36), primary_key=True)
    name = Column(String)
    slug = Column(String, unique=True)
    nib = Column(String)
    nib_verified = Column(Boolean, default=False)
    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)
    completed_bookings = Column(Integer, default=0)
    address = Column(String)
    district = Column(String)
    city = Column(String)
    phone = Column(String)
    whatsapp = Column(String)
    operating_hours = Column(String)
    description = Column(String)
    avatar_url = Column(String)
    banner_url = Column(String)
    established_year = Column(Integer)
    coverage_spot_ids = Column(JSON, default=list)
    features = Column(JSON, default=list)
    reviews = Column(JSON, default=list)  # list of RentalReview dicts


class MarketplaceVehicle(Base):
    __tablename__ = "marketplace_vehicles"
    id = Column(String(36), primary_key=True)
    rental_id = Column(String(36), index=True)
    rental_name = Column(String)
    rental_rating = Column(Float, default=0)
    rental_completed_bookings = Column(Integer, default=0)
    name = Column(String)
    brand = Column(String)
    model = Column(String)
    year = Column(Integer)
    license_plate = Column(String, index=True)
    category = Column(String, index=True)
    transmission = Column(String)
    fuel_type = Column(String)
    seating_capacity = Column(Integer)
    luggage_capacity = Column(Integer)
    engine_capacity_cc = Column(Integer)
    features = Column(JSON, default=list)
    thumbnail_url = Column(String)
    gallery_images = Column(JSON, default=list)
    status = Column(String, default="TERSEDIA")
    base_daily_rate = Column(BigInteger)
    security_deposit = Column(BigInteger)
    delivery_fee = Column(BigInteger, default=0)
    city = Column(String)
    district = Column(String)
    garage_address = Column(String)
    last_updated_at = Column(DateTime(timezone=True), default=utcnow)
    is_popular = Column(Boolean, default=False)
    # Fase 8 fleet attributes
    stnk_number = Column(String, nullable=True)
    stnk_tax_expiry_date = Column(String, nullable=True)
    stnk_photo_url = Column(String, nullable=True)
    odometer_km = Column(Integer, nullable=True)
    next_service_km = Column(Integer, nullable=True)
    next_service_date = Column(String, nullable=True)
    equipment_checklist = Column(JSON, nullable=True)
    service_history = Column(JSON, nullable=True)


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    id = Column(String(36), primary_key=True)
    rental_id = Column(String(36), index=True)
    rental_name = Column(String)
    vehicle_id = Column(String(36), index=True)
    vehicle_name = Column(String)
    vehicle_plate = Column(String)
    vehicle_category = Column(String)
    vehicle_transmission = Column(String)
    thumbnail_url = Column(String)
    service_type = Column(String, default="LEPAS_KUNCI")
    base_daily_rate = Column(BigInteger)
    driver_daily_rate = Column(BigInteger, nullable=True)
    security_deposit = Column(BigInteger)
    weekend_surcharge = Column(BigInteger, default=0)
    spot_delivery_rates = Column(JSON, default=list)
    minimum_rental_days = Column(Integer, default=1)
    included_facilities = Column(JSON, default=list)
    rental_terms = Column(JSON, default=list)
    status = Column(String, default="AKTIF")
    last_freshness_confirmed_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow)


class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(String(36), primary_key=True)
    ticket_code = Column(String, unique=True)
    booking_id = Column(String(36), index=True)
    booking_code = Column(String)
    vehicle_name = Column(String)
    vehicle_thumbnail = Column(String)
    rental_name = Column(String)
    category = Column(String)
    description = Column(String)
    claimed_amount = Column(BigInteger)
    demands = Column(String)
    renter_evidence_urls = Column(JSON, default=list)
    partner_evidence_urls = Column(JSON, default=list)
    status = Column(String)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    timeline = Column(JSON, default=list)
    mediator_verdict = Column(JSON, nullable=True)


class InAppNotification(Base):
    __tablename__ = "in_app_notifications"
    id = Column(String(36), primary_key=True)
    title = Column(String)
    message = Column(String)
    category = Column(String, default="TRANSAKSI")
    timestamp = Column(DateTime(timezone=True), default=utcnow)
    is_read = Column(Boolean, default=False)
    link_url = Column(String, default="")
