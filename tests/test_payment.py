import pytest
from app.modules.payment.service import signature_for, create_payment_intent, handle_notification
from app.modules.payment.schemas import MidtransNotification
from app.core.enums import PaymentType, PaymentStatus, BookingState
from app.core.errors import Conflict
import uuid
import hashlib

def test_signature():
    # sha512(order_id + status_code + gross_amount + settings.midtrans_server_key).hexdigest()
    # settings.midtrans_server_key is "dev-server-key"
    order = "123"
    code = "200"
    amount = "50000.00"
    expected = hashlib.sha512(f"{order}{code}{amount}dev-server-key".encode()).hexdigest()
    assert signature_for(order, code, amount) == expected

async def test_create_intent_dp_when_menunggu_dp(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o1@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_DP)
    payment = await create_payment_intent(db, booking, PaymentType.DP)
    assert payment.amount == booking.dp
    assert payment.type == PaymentType.DP
    assert payment.status == PaymentStatus.PENDING

async def test_create_intent_pelunasan_when_terkonfirmasi(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o2@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    payment = await create_payment_intent(db, booking, PaymentType.PELUNASAN)
    assert payment.amount == booking.sisa
    assert payment.type == PaymentType.PELUNASAN

async def test_create_intent_wrong_state_raises_409(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o3@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.TERKONFIRMASI)
    with pytest.raises(Conflict):
        await create_payment_intent(db, booking, PaymentType.DP)

async def test_late_dp_webhook_refunds(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="lateo@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    # Booking already expired
    booking = await make_booking(db, penyewa, listing, state=BookingState.DIBATALKAN)
    
    # create_payment_intent will raise 409 because booking is DIBATALKAN, so we cannot create DP intent this way.
    # We should directly create the payment instead.
    from app.modules.payment.models import Payment
    intent = Payment(booking_id=booking.id, type=PaymentType.DP, order_id=f"{booking.id}-DP", amount=booking.dp, status=PaymentStatus.PENDING)
    db.add(intent)
    await db.commit()

    sig = signature_for(intent.order_id, "200", str(float(booking.dp)))
    payload = MidtransNotification(
        order_id=intent.order_id, status_code="200", gross_amount=str(float(booking.dp)),
        signature_key=sig, transaction_status="settlement", transaction_id="trx1"
    )
    
    payment = await handle_notification(db, payload)
    await db.commit()
    
    assert payment.status == PaymentStatus.BERHASIL
    assert booking.booking_state == BookingState.DIBATALKAN
    
    # Check refund was issued
    from app.modules.payment.escrow import balance
    bal = await balance(db, booking.id)
    assert bal == 0

async def test_duplicate_webhook_idempotent(db, client):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="dupo@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_DP)
    
    intent = await create_payment_intent(db, booking, PaymentType.DP)
    await db.commit()

    sig = signature_for(intent.order_id, "200", str(float(booking.dp)))
    payload = MidtransNotification(
        order_id=intent.order_id, status_code="200", gross_amount=str(float(booking.dp)),
        signature_key=sig, transaction_status="settlement", transaction_id="trx2"
    )
    
    p1 = await handle_notification(db, payload)
    await db.commit()
    
    p2 = await handle_notification(db, payload)
    await db.commit()
    
    assert p1.id == p2.id
    
    from app.modules.payment.escrow import balance
    bal = await balance(db, booking.id)
    assert bal == booking.dp # Only held once

async def test_api_create_intent(client, db):
    from tests.factories import make_booking, make_user, make_listing, make_vehicle, make_rental, auth_header
    penyewa = await make_user(db)
    rental_owner = await make_user(db, email="o5@x.com")
    rental = await make_rental(db, rental_owner)
    vehicle = await make_vehicle(db, rental)
    listing = await make_listing(db, vehicle)
    booking = await make_booking(db, penyewa, listing, state=BookingState.MENUNGGU_DP)
    
    headers = auth_header(penyewa)
    resp = await client.post(f"/bookings/{booking.id}/payments", json={"type": "DP"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["order_id"] == f"{booking.id}-DP"
    assert data["status"] == "PENDING"
    assert "redirect_url" in data
