from pydantic import ConfigDict
from app.core.schemas import ResponseModel


class PickupSpotResponse(ResponseModel):
    id: str
    name: str
    code: str
    area: str
    description: str
    extraFee: int
    isPopular: bool
    estimatedDeliveryMin: int

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            name=row.name,
            code=row.code,
            area=row.area,
            description=row.description,
            extraFee=row.extra_fee,
            isPopular=row.is_popular,
            estimatedDeliveryMin=row.estimated_delivery_min,
        )


class RentalResponse(ResponseModel):
    id: str
    name: str
    slug: str
    nib: str
    nibVerified: bool
    rating: float
    totalReviews: int
    completedBookings: int
    address: str
    district: str
    city: str
    phone: str
    whatsapp: str
    operatingHours: str
    description: str
    avatarUrl: str
    bannerUrl: str
    establishedYear: int
    coverageSpotIds: list[str]
    features: list[str]
    reviews: list[dict]

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            name=row.name,
            slug=row.slug,
            nib=row.nib,
            nibVerified=row.nib_verified,
            rating=row.rating,
            totalReviews=row.total_reviews,
            completedBookings=row.completed_bookings,
            address=row.address,
            district=row.district,
            city=row.city,
            phone=row.phone,
            whatsapp=row.whatsapp,
            operatingHours=row.operating_hours,
            description=row.description,
            avatarUrl=row.avatar_url,
            bannerUrl=row.banner_url,
            establishedYear=row.established_year,
            coverageSpotIds=row.coverage_spot_ids or [],
            features=row.features or [],
            reviews=row.reviews or [],
        )


class VehicleResponse(ResponseModel):
    id: str
    rentalId: str
    rentalName: str
    rentalRating: float
    rentalCompletedBookings: int
    name: str
    brand: str
    model: str
    year: int
    licensePlate: str
    category: str
    transmission: str
    fuelType: str
    seatingCapacity: int
    luggageCapacity: int
    engineCapacityCc: int
    features: list[str]
    thumbnailUrl: str
    galleryImages: list[str]
    status: str
    baseDailyRate: int
    securityDeposit: int
    deliveryFee: int
    city: str
    district: str
    garageAddress: str
    lastUpdatedAt: str
    isPopular: bool
    stnkNumber: str | None = None
    stnkTaxExpiryDate: str | None = None
    stnkPhotoUrl: str | None = None
    odometerKm: int | None = None
    nextServiceKm: int | None = None
    nextServiceDate: str | None = None
    equipmentChecklist: dict | None = None
    serviceHistory: list[dict] | None = None

    @classmethod
    def from_row(cls, row):
        import json
        base = dict(
            id=row.id,
            rentalId=row.rental_id,
            rentalName=row.rental_name,
            rentalRating=row.rental_rating,
            rentalCompletedBookings=row.rental_completed_bookings,
            name=row.name,
            brand=row.brand,
            model=row.model,
            year=row.year,
            licensePlate=row.license_plate,
            category=row.category,
            transmission=row.transmission,
            fuelType=row.fuel_type,
            seatingCapacity=row.seating_capacity,
            luggageCapacity=row.luggage_capacity,
            engineCapacityCc=row.engine_capacity_cc,
            features=row.features or [],
            thumbnailUrl=row.thumbnail_url,
            galleryImages=row.gallery_images or [],
            status=row.status,
            baseDailyRate=row.base_daily_rate,
            securityDeposit=row.security_deposit,
            deliveryFee=row.delivery_fee or 0,
            city=row.city,
            district=row.district,
            garageAddress=row.garage_address,
            lastUpdatedAt=row.last_updated_at.isoformat() if row.last_updated_at else "",
            isPopular=bool(row.is_popular),
            stnkNumber=row.stnk_number,
            stnkTaxExpiryDate=row.stnk_tax_expiry_date,
            stnkPhotoUrl=row.stnk_photo_url,
            odometerKm=row.odometer_km,
            nextServiceKm=row.next_service_km,
            nextServiceDate=row.next_service_date,
            equipmentChecklist=row.equipment_checklist,
            serviceHistory=row.service_history,
        )
        return cls(**base)


class ListingResponse(ResponseModel):
    id: str
    rentalId: str
    rentalName: str
    vehicleId: str
    vehicleName: str
    vehiclePlate: str
    vehicleCategory: str
    vehicleTransmission: str
    thumbnailUrl: str
    serviceType: str
    baseDailyRate: int
    driverDailyRate: int | None = None
    securityDeposit: int
    weekendSurcharge: int
    spotDeliveryRates: list[dict]
    minimumRentalDays: int
    includedFacilities: list[str]
    rentalTerms: list[str]
    status: str
    lastFreshnessConfirmedAt: str
    createdAt: str
    updatedAt: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            rentalId=row.rental_id,
            rentalName=row.rental_name,
            vehicleId=row.vehicle_id,
            vehicleName=row.vehicle_name,
            vehiclePlate=row.vehicle_plate,
            vehicleCategory=row.vehicle_category,
            vehicleTransmission=row.vehicle_transmission,
            thumbnailUrl=row.thumbnail_url,
            serviceType=row.service_type,
            baseDailyRate=row.base_daily_rate,
            driverDailyRate=row.driver_daily_rate,
            securityDeposit=row.security_deposit,
            weekendSurcharge=row.weekend_surcharge,
            spotDeliveryRates=row.spot_delivery_rates or [],
            minimumRentalDays=row.minimum_rental_days,
            includedFacilities=row.included_facilities or [],
            rentalTerms=row.rental_terms or [],
            status=row.status,
            lastFreshnessConfirmedAt=row.last_freshness_confirmed_at.isoformat() if row.last_freshness_confirmed_at else "",
            createdAt=row.created_at.isoformat() if row.created_at else "",
            updatedAt=row.updated_at.isoformat() if row.updated_at else "",
        )


class DisputeResponse(ResponseModel):
    id: str
    ticketCode: str
    bookingId: str
    bookingCode: str
    vehicleName: str
    vehicleThumbnail: str
    rentalName: str
    category: str
    description: str
    claimedAmount: int
    demands: str
    renterEvidenceUrls: list[str]
    partnerEvidenceUrls: list[str]
    status: str
    createdAt: str
    timeline: list[dict]
    mediatorVerdict: dict | None = None

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            ticketCode=row.ticket_code,
            bookingId=row.booking_id,
            bookingCode=row.booking_code,
            vehicleName=row.vehicle_name,
            vehicleThumbnail=row.vehicle_thumbnail,
            rentalName=row.rental_name,
            category=row.category,
            description=row.description,
            claimedAmount=row.claimed_amount,
            demands=row.demands,
            renterEvidenceUrls=row.renter_evidence_urls or [],
            partnerEvidenceUrls=row.partner_evidence_urls or [],
            status=row.status,
            createdAt=row.created_at.isoformat() if row.created_at else "",
            timeline=row.timeline or [],
            mediatorVerdict=row.mediator_verdict,
        )


class NotificationResponse(ResponseModel):
    id: str
    title: str
    message: str
    category: str
    timestamp: str
    isRead: bool
    linkUrl: str

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row.id,
            title=row.title,
            message=row.message,
            category=row.category,
            timestamp=row.timestamp.isoformat() if row.timestamp else "",
            isRead=bool(row.is_read),
            linkUrl=row.link_url or "",
        )