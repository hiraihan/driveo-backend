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
from app.core.time import today_wib, utcnow
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

from app.core.enums import UserRole, BookingEvent
from app.modules.rental.service import get_rental_id_for_staff
from app.modules.booking.state import transition
from app.modules.availability.service import release_slots
from app.modules.refund.service import calculate_refund_amount, RefundService
from app.modules.payment import escrow
from app.modules.notification.service import NotificationService
from app.modules.user.service import get_user

async def get_booking_for_actor(db: AsyncSession, booking_id: str, actor: CurrentUser) -> Booking:
    booking = await get_booking(db, booking_id)
    if actor.role == UserRole.ADMIN:
        return booking
    if booking.user_id == actor.id:
        return booking
    staff_rental_id = await get_rental_id_for_staff(db, actor.id)
    if staff_rental_id and booking.rental_id == staff_rental_id:
        return booking
    raise Forbidden("Akses ditolak")

async def cancel_booking(db: AsyncSession, booking: Booking, actor_id: str | None, alasan: str | None, by_rental: bool) -> Booking:
    # 1. Transition state
    booking.booking_state = transition(booking, BookingEvent.CANCEL)
    booking.alasan_batal = alasan
    booking.dibatalkan_oleh = actor_id
    
    # 2. Release slots
    await release_slots(db, booking.id)
    
    # 3. Calculate refund
    current_balance = await escrow.balance(db, booking.id)
    if current_balance > 0:
        if by_rental:
            refund_amount = current_balance
        else:
            refund_amount = calculate_refund_amount(current_balance, booking.tanggal_mulai, today_wib())
            
        if refund_amount > 0:
            await RefundService(db).trigger_refund(booking.id, refund_amount, "CANCEL")
            
        remainder = await escrow.balance(db, booking.id)
        if remainder > 0:
            await escrow.release(db, booking.id, "CANCEL_FORFEIT")
            
        if refund_amount > 0:
            booking.escrow_state = EscrowState.DIKEMBALIKAN
        elif remainder > 0:
            booking.escrow_state = EscrowState.DICAIRKAN
        else:
            booking.escrow_state = EscrowState.NONE
    else:
        booking.escrow_state = EscrowState.NONE
            
    await AuditService(db).log_event("BOOKING_CANCELLED", {"booking_id": booking.id, "alasan": alasan}, actor_id=actor_id)
    
    penyewa = await get_user(db, booking.user_id)
    if penyewa:
        await NotificationService(db).send(penyewa.email, f"Booking {booking.id} dibatalkan.", subject="Booking Dibatalkan")
        
    return booking

from datetime import datetime

async def confirm_booking(db: AsyncSession, booking: Booking, actor_id: str) -> Booking:
    booking.booking_state = transition(booking, BookingEvent.CONFIRM)
    booking.confirmed_at = utcnow()
    
    await AuditService(db).log_event("BOOKING_CONFIRMED", {"booking_id": booking.id}, actor_id=actor_id)
    
    penyewa = await get_user(db, booking.user_id)
    if penyewa:
        await NotificationService(db).send(penyewa.email, f"Booking {booking.id} dikonfirmasi oleh rental.", subject="Booking Dikonfirmasi")
    return booking

async def reject_booking(db: AsyncSession, booking: Booking, actor_id: str, alasan: str) -> Booking:
    booking.booking_state = transition(booking, BookingEvent.REJECT)
    booking.alasan_batal = alasan
    
    await release_slots(db, booking.id)
    
    current_balance = await escrow.balance(db, booking.id)
    if current_balance > 0:
        await RefundService(db).trigger_refund(booking.id, current_balance, "REJECTED_BY_RENTAL")
        booking.escrow_state = EscrowState.DIKEMBALIKAN
    
    await AuditService(db).log_event("BOOKING_REJECTED", {"booking_id": booking.id, "alasan": alasan}, actor_id=actor_id)
    
    penyewa = await get_user(db, booking.user_id)
    if penyewa:
        await NotificationService(db).send(penyewa.email, f"Booking {booking.id} ditolak: {alasan}", subject="Booking Ditolak")
    return booking

async def expire_unpaid_bookings(db: AsyncSession, now: datetime) -> int:
    settings = get_settings()
    from datetime import timedelta
    limit = now - timedelta(minutes=settings.dp_expiry_minutes)
    
    stmt = select(Booking).where(Booking.booking_state == BookingState.MENUNGGU_DP).where(Booking.created_at < limit)
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    
    count = 0
    for booking in bookings:
        booking.booking_state = transition(booking, BookingEvent.EXPIRE)
        await release_slots(db, booking.id)
        await AuditService(db).log_event("BOOKING_EXPIRED", {"booking_id": booking.id})
        count += 1
    return count

async def breach_unconfirmed_bookings(db: AsyncSession, now: datetime) -> int:
    settings = get_settings()
    from datetime import timedelta
    limit = now - timedelta(minutes=settings.rental_confirm_sla_minutes)
    
    stmt = select(Booking).where(Booking.booking_state == BookingState.MENUNGGU_KONFIRMASI_RENTAL).where(Booking.dp_paid_at < limit)
    result = await db.execute(stmt)
    bookings = result.scalars().all()
    
    count = 0
    for booking in bookings:
        booking.booking_state = transition(booking, BookingEvent.SLA_BREACH)
        await release_slots(db, booking.id)
        
        current_balance = await escrow.balance(db, booking.id)
        if current_balance > 0:
            await RefundService(db).trigger_refund(booking.id, current_balance, "SLA_BREACH")
            booking.escrow_state = EscrowState.DIKEMBALIKAN
            
        await AuditService(db).log_event("BOOKING_SLA_BREACH", {"booking_id": booking.id})
        count += 1
    return count
