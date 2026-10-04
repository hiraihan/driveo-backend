import pytest
from typing import Protocol

def test_booking_port_exists():
    from app.contracts.ports import BookingPort
    assert issubclass(BookingPort, Protocol)
    assert hasattr(BookingPort, "get_booking")

def test_rental_read_port_exists():
    from app.contracts.ports import RentalReadPort
    assert issubclass(RentalReadPort, Protocol)
    assert hasattr(RentalReadPort, "get_rental_status")

def test_payment_read_port_exists():
    from app.contracts.ports import PaymentReadPort
    assert issubclass(PaymentReadPort, Protocol)

def test_escrow_read_port_exists():
    from app.contracts.ports import EscrowReadPort
    assert issubclass(EscrowReadPort, Protocol)

def test_verification_read_port_exists():
    from app.contracts.ports import VerificationReadPort
    assert issubclass(VerificationReadPort, Protocol)

def test_refund_port_exists():
    from app.contracts.ports import RefundPort
    assert issubclass(RefundPort, Protocol)

def test_notification_port_exists():
    from app.contracts.ports import NotificationPort
    assert issubclass(NotificationPort, Protocol)

def test_audit_port_exists():
    from app.contracts.ports import AuditPort
    assert issubclass(AuditPort, Protocol)
    assert hasattr(AuditPort, "log_event")
