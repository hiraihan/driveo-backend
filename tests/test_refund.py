
from tests.factories import make_user, make_rental, make_vehicle, make_listing, make_booking

async def get_b1(db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    l = await make_listing(db, v)
    b1 = await make_booking(db, u, l)
    return b1.id
import pytest
from datetime import date
from app.modules.refund.service import calculate_refund_amount, RefundService
from app.modules.payment.escrow import hold, balance
from app.modules.audit.models import AuditLog
from sqlalchemy import select
from app.core.enums import EscrowState

def test_refund_tiers():
    # >= 2 days => 100% of paid_amount
    assert calculate_refund_amount(300000, date(2026, 12, 10), date(2026, 12, 8)) == 300000
    # == 1 day => 50% of paid_amount
    assert calculate_refund_amount(300000, date(2026, 12, 10), date(2026, 12, 9)) == 150000
    # 0 days => 0
    assert calculate_refund_amount(300000, date(2026, 12, 10), date(2026, 12, 10)) == 0

async def test_refund_service_trigger(db):
    b1 = await get_b1(db)
    await hold(db, b1, 500000, "REF-1")
    await db.commit()
    svc = RefundService(db)
    r_id = await svc.trigger_refund(b1, 200000, "TEST")
    await db.commit()
    assert r_id != ""
    assert await balance(db, b1) == 300000
    # Audit log check
    row = (await db.execute(select(AuditLog).where(AuditLog.event_name == "REFUND_ISSUED"))).scalar_one()
    assert row is not None

async def test_refund_service_zero_amount(db):
    svc = RefundService(db)
    r_id = await svc.trigger_refund("b2", 0, "TEST")
    assert r_id == ""
