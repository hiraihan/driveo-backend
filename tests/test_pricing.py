from datetime import date
from app.modules.booking.pricing import quote, Quote
from app.modules.admin.models import Promo

def test_quote_single_day_and_rounding():
    q = quote(333_333, date(2026, 12, 1), date(2026, 12, 1), None, 30.0)
    assert (q.hari, q.subtotal, q.dp, q.dp + q.sisa) == (1, 333_333, 100_000, 333_333)

def test_quote_promo_capped():
    promo = Promo(discount_percent=50.0, max_discount_amount=100_000)
    q = quote(300_000, date(2026, 12, 1), date(2026, 12, 3), promo, 30.0)
    assert (q.subtotal, q.diskon, q.total_nilai) == (900_000, 100_000, 800_000)
