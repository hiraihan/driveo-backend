from app.contracts.ports import *
from app.core.enums import VerificationStatus, RentalStatus, EscrowState

class MockAuditPort:
    async def log_event(self, event_name: str, payload: dict, actor_id: str | None = None) -> None:
        pass

class MockNotificationPort:
    async def send(self, recipient: str, message: str, subject: str | None = None, channel: str = "EMAIL") -> None:
        pass

class MockVerificationReadPort:
    async def get_status(self, user_id: str) -> VerificationStatus:
        return VerificationStatus.TERVERIFIKASI

class MockRentalReadPort:
    async def get_rental_status(self, rental_id: str) -> RentalStatus:
        return RentalStatus.LOLOS

class MockRefundPort:
    async def trigger_refund(self, booking_id: str, amount: int, reason: str) -> str:
        return "REFUND_123"

class MockEscrowReadPort:
    async def get_state(self, booking_id: str) -> EscrowState:
        return EscrowState.LUNAS
