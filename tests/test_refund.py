import pytest
from app.modules.refund.service import calculate_refund_amount
from datetime import datetime, date

def test_refund_calculation_h_minus_2():
    # H-2 cancellation should be 100% of total
    amount = calculate_refund_amount(1000000, 300000, date(2026, 12, 5), date(2026, 12, 1))
    assert amount == 1000000

def test_refund_calculation_h_minus_1():
    # H-1 cancellation should be 50%
    amount = calculate_refund_amount(1000000, 300000, date(2026, 12, 5), date(2026, 12, 4))
    assert amount == 500000
