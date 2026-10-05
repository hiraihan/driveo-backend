from typing import Protocol, runtime_checkable
from app.core.enums import VerificationStatus, RentalStatus, EscrowState

@runtime_checkable
class AuditPort(Protocol):
    async def log_event(self, event_name: str, payload: dict, actor_id: str | None = None) -> None: ...

@runtime_checkable
class NotificationPort(Protocol):
    async def send(self, recipient: str, message: str, subject: str | None = None, channel: str = "EMAIL") -> None: ...

@runtime_checkable
class VerificationReadPort(Protocol):
    async def get_status(self, user_id: str) -> VerificationStatus: ...

@runtime_checkable
class RentalReadPort(Protocol):
    async def get_rental_status(self, rental_id: str) -> RentalStatus: ...

@runtime_checkable
class RefundPort(Protocol):
    async def trigger_refund(self, booking_id: str, amount: int, reason: str) -> str: ...

@runtime_checkable
class EscrowReadPort(Protocol):
    async def get_state(self, booking_id: str) -> EscrowState: ...
