import pytest
from typing import Dict, Any

def test_mock_payment_read_port():
    from app.mocks.ports import MockPaymentReadPort
    port = MockPaymentReadPort()
    assert port.get_status("some_id") == "BERHASIL"

def test_mock_audit_port():
    from app.mocks.ports import MockAuditPort
    port = MockAuditPort()
    port.log_event("TEST", {"key": "value"})
    # Should not raise exception and should print, we can just assert it exists and is callable
    assert hasattr(port, "log_event")

def test_mock_escrow_read_port():
    from app.mocks.ports import MockEscrowReadPort
    port = MockEscrowReadPort()
    assert port.get_state("some_id") == "LUNAS"
