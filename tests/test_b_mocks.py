import pytest
from app.mocks.ports import MockBookingPort, MockRentalReadPort

def test_mock_booking_port():
    port = MockBookingPort()
    assert port.get_booking("test_id") == {"id": "test_id", "status": "MENUNGGU_DP", "total_nilai": 1000000, "dp": 300000}

def test_mock_rental_read_port():
    port = MockRentalReadPort()
    assert port.get_rental_status("test_id") == "LOLOS"
