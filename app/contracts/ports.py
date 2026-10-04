from typing import Protocol, Any, Dict

class BookingPort(Protocol):
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        ...

class RentalReadPort(Protocol):
    def get_rental_status(self, rental_id: str) -> str:
        ...

class PaymentReadPort(Protocol):
    pass

class EscrowReadPort(Protocol):
    pass

class VerificationReadPort(Protocol):
    pass

class RefundPort(Protocol):
    pass

class NotificationPort(Protocol):
    pass

class AuditPort(Protocol):
    def log_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        ...
