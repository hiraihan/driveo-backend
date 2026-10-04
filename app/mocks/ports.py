from typing import Dict, Any

class MockPaymentReadPort:
    def get_status(self, payment_id: str) -> str:
        return "BERHASIL"

class MockAuditPort:
    def log_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        print(f"AUDIT LOG: {event_name} - {payload}")

class MockEscrowReadPort:
    def get_state(self, booking_id: str) -> str:
        return "LUNAS"

class MockVerificationReadPort:
    def get_status(self, user_id: str) -> str:
        return "TERVERIFIKASI"

class MockRefundPort:
    def trigger_refund(self, booking_id: str, amount: float) -> str:
        return "REFUND_SUCCESS"

class MockNotificationPort:
    def send(self, recipient: str, message: str) -> None:
        print(f"NOTIFICATION to {recipient}: {message}")
