from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.booking.models import Booking
from app.modules.booking.schemas import BookingCreate
from app.modules.booking.pricing import quote
from app.modules.listing.service import get_published_listing
from app.modules.admin.service import get_valid_promo
from app.modules.availability.service import lock_slots
from app.modules.verification.service import VerificationService
from app.core.enums import VerificationStatus, BookingState, EscrowState
from app.core.errors import NotFound, ValidationFailed, AppError, Conflict, Forbidden
from app.core.time import today_wib
from app.core.config import get_settings
from app.modules.auth.dependencies import CurrentUser
from app.modules.audit.service import AuditService

async def get_booking(db: AsyncSession, booking_id: str) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise NotFound("Booking tidak ditemukan")
    return booking

async def create_booking(db: AsyncSession, user: CurrentUser, req: BookingCreate) -> Booking:
    if req.tanggal_mulai < today_wib():
        raise ValidationFailed("DATE_IN_PAST", "Tanggal mulai tidak boleh di masa lalu")
    if req.tanggal_selesai < req.tanggal_mulai:
        raise ValidationFailed("DATE_RANGE_INVALID", "Tanggal selesai tidak boleh sebelum tanggal mulai")
        
    v_status = await VerificationService(db).get_status(user.id)
    if v_status != VerificationStatus.TERVERIFIKASI:
        raise AppError(code="KYC_REQUIRED", message="Akun belum terverifikasi", status_code=403)

    listing = await get_published_listing(db, req.listing_id)
    
    promo = None
    if req.promo_code:
        promo = await get_valid_promo(db, req.promo_code, today_wib())
        
    settings = get_settings()
    
    q = quote(
        harga_per_hari=listing.harga_all_in,
        tanggal_mulai=req.tanggal_mulai,
        tanggal_selesai=req.tanggal_selesai,
        promo=promo,
        dp_percent=settings.dp_percent
    )
    
    from app.core.ids import new_id
    booking_id = new_id()
    
    await lock_slots(db, listing.vehicle_id, req.tanggal_mulai, req.tanggal_selesai, booking_id)
    
    booking = Booking(
        id=booking_id,
        user_id=user.id,
        rental_id=listing.rental_id,
        vehicle_id=listing.vehicle_id,
        listing_id=listing.id,
        tanggal_mulai=req.tanggal_mulai,
        tanggal_selesai=req.tanggal_selesai,
        hari=q.hari,
        harga_per_hari=q.harga_per_hari,
        subtotal=q.subtotal,
        diskon=q.diskon,
        promo_id=promo.id if promo else None,
        total_nilai=q.total_nilai,
        dp=q.dp,
        sisa=q.sisa,
        booking_state=BookingState.MENUNGGU_DP.value,
        escrow_state=EscrowState.NONE.value
    )
    
    db.add(booking)
    
    await AuditService(db).log_event("BOOKING_CREATED", {"booking_id": booking.id}, actor_id=user.id)
    
    return booking
