from typing import Protocol, Any, Dict

class BookingPort(Protocol):
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        ...

class RentalReadPort(Protocol):
    def get_rental_status(self, rental_id: str) -> str:
        ...

class PaymentReadPort(Protocol):
    def get_status(self, payment_id: str) -> str:
        ...

class EscrowReadPort(Protocol):
    def get_state(self, booking_id: str) -> str:
        ...

class VerificationReadPort(Protocol):
    def get_status(self, user_id: str) -> str:
        ...

class RefundPort(Protocol):
    def trigger_refund(self, booking_id: str, amount: float) -> str:
        ...

class NotificationPort(Protocol):
    def send(self, recipient: str, message: str) -> None:
        ...

class AuditPort(Protocol):
    def log_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        ...
