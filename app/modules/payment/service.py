import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.payment.models import Payment
from app.modules.payment.schemas import MidtransNotification
from app.core.config import get_settings
from app.core.enums import PaymentType, PaymentStatus, BookingState, BookingEvent, EscrowState
from app.core.errors import Conflict, NotFound, Unauthorized, ValidationFailed
from app.modules.booking.models import Booking
from app.modules.payment import escrow
from app.modules.booking.state import transition
from app.core.time import utcnow
from app.modules.audit.service import AuditService
from app.modules.notification.service import NotificationService
from app.contracts.ports import RefundPort

def signature_for(order_id: str, status_code: str, gross_amount: str) -> str:
    settings = get_settings()
    raw = f"{order_id}{status_code}{gross_amount}{settings.midtrans_server_key}"
    return hashlib.sha512(raw.encode()).hexdigest()

async def create_payment_intent(db: AsyncSession, booking: Booking, type: PaymentType) -> Payment:
    if type == PaymentType.DP:
        if booking.booking_state != BookingState.MENUNGGU_DP:
            raise Conflict("PAYMENT_NOT_ALLOWED", "DP hanya bisa dibayar saat status MENUNGGU_DP")
        amount = booking.dp
    elif type == PaymentType.PELUNASAN:
        if booking.booking_state != BookingState.TERKONFIRMASI:
            raise Conflict("PAYMENT_NOT_ALLOWED", "Pelunasan hanya bisa dibayar saat status TERKONFIRMASI")
        amount = booking.sisa
    else:
        raise Conflict("PAYMENT_NOT_ALLOWED", "Tipe pembayaran tidak valid")

    order_id = f"{booking.id}-{type.value}"

    stmt = select(Payment).where(Payment.order_id == order_id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    
    if existing:
        if existing.status == PaymentStatus.PENDING:
            return existing
        else:
            raise Conflict("PAYMENT_ALREADY_PROCESSED", "Pembayaran ini sudah diproses")

    payment = Payment(
        booking_id=booking.id,
        type=type,
        order_id=order_id,
        amount=amount,
        status=PaymentStatus.PENDING
    )
    db.add(payment)
    return payment

async def handle_notification(db: AsyncSession, payload: MidtransNotification, refund_service: RefundPort = None) -> Payment:
    expected_sig = signature_for(payload.order_id, payload.status_code, payload.gross_amount)
    if payload.signature_key != expected_sig:
        raise Unauthorized(code="INVALID_SIGNATURE", message="Signature webhook tidak valid")

    stmt = select(Payment).where(Payment.order_id == payload.order_id)
    payment = (await db.execute(stmt)).scalar_one_or_none()
    
    if not payment:
        raise NotFound("Pembayaran tidak ditemukan")

    # If it's already final, idempotent
    if payment.status in {PaymentStatus.BERHASIL, PaymentStatus.GAGAL}:
        return payment

    # Validate amount
    try:
        gross_amount_int = int(float(payload.gross_amount))
    except ValueError:
        raise ValidationFailed("AMOUNT_MISMATCH", "Format gross_amount tidak valid")

    if gross_amount_int != payment.amount:
        raise ValidationFailed("AMOUNT_MISMATCH", "Jumlah pembayaran tidak sesuai")

    if payload.transaction_status in {"settlement", "capture"}:
        new_status = PaymentStatus.BERHASIL
    elif payload.transaction_status in {"expire", "cancel", "deny"}:
        new_status = PaymentStatus.GAGAL
    else:
        new_status = PaymentStatus.PENDING

    if new_status == payment.status:
        # e.g., still PENDING (maybe "pending" status from midtrans)
        payment.transaction_id = payload.transaction_id
        return payment

    payment.status = new_status
    payment.transaction_id = payload.transaction_id

    if new_status == PaymentStatus.BERHASIL:
        payment.paid_at = utcnow()
        
        # Escrow hold
        await escrow.hold(db, payment.booking_id, payment.amount, reference=payment.order_id)
        
        # Load booking
        b_stmt = select(Booking).where(Booking.id == payment.booking_id)
        booking = (await db.execute(b_stmt)).scalar_one()

        if payment.type == PaymentType.DP:
            if booking.booking_state == BookingState.MENUNGGU_DP:
                booking.booking_state = transition(booking, BookingEvent.DP_PAID)
                booking.escrow_state = EscrowState.DITAHAN_ESCROW
                booking.dp_paid_at = utcnow()
            elif booking.booking_state == BookingState.DIBATALKAN:
                # Late payment -> Refund
                if refund_service:
                    await refund_service.trigger_refund(booking.id, payment.amount, "LATE_PAYMENT")
                else:
                    await escrow.refund(db, booking.id, payment.amount, f"LATE-{payment.order_id}")
        elif payment.type == PaymentType.PELUNASAN:
            # We don't transition state here according to table, state transitions to BERJALAN on HANDOVER.
            # But we update escrow state
            booking.escrow_state = EscrowState.LUNAS

        await AuditService(db).log_event("PAYMENT_RECEIVED", {"order_id": payment.order_id, "amount": payment.amount})
        # Note: Notification needs recipient. In real implementation we'd get the user email.
        # But we don't have user eagerly loaded. Let's do it if needed.
        # It says "notify penyewa" -> we need user email.
        # For simplicity in tests, assume user is joined or we fetch user.
        from app.modules.user.models import User
        u_stmt = select(User).where(User.id == booking.user_id)
        user = (await db.execute(u_stmt)).scalar_one_or_none()
        if user:
            await NotificationService(db).send(user.email, f"Pembayaran {payment.type} untuk booking {booking.id} berhasil.", subject="Pembayaran Berhasil")

    return payment
