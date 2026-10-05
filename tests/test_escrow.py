
from tests.factories import make_user, make_rental, make_vehicle, make_listing, make_booking

async def get_b1_b2(db):
    u = await make_user(db)
    r = await make_rental(db, u)
    v = await make_vehicle(db, r)
    l = await make_listing(db, v)
    b1 = await make_booking(db, u, l)
    b2 = await make_booking(db, u, l)
    return b1.id, b2.id
import pytest
from app.modules.payment.escrow import hold, balance, release, refund, totals_for_bookings
from app.core.errors import Conflict
import uuid

async def test_escrow_hold_and_balance(db):
    b_id, _ = await get_b1_b2(db)
    await hold(db, b_id, 100000, "REF-1")
    await hold(db, b_id, 50000, "REF-2")
    await db.commit()
    assert await balance(db, b_id) == 150000

async def test_escrow_release(db):
    b_id, _ = await get_b1_b2(db)
    await hold(db, b_id, 100000, "REF-1")
    amount = await release(db, b_id, "REL-1")
    await db.commit()
    assert amount == 100000
    assert await balance(db, b_id) == 0

async def test_escrow_release_empty(db):
    b_id, _ = await get_b1_b2(db)
    amount = await release(db, b_id, "REL-1")
    assert amount == 0
    assert await balance(db, b_id) == 0

async def test_escrow_refund(db):
    b_id, _ = await get_b1_b2(db)
    await hold(db, b_id, 100000, "REF-1")
    await refund(db, b_id, 40000, "RFND-1")
    await db.commit()
    assert await balance(db, b_id) == 60000

async def test_escrow_refund_exceeds(db):
    b_id, _ = await get_b1_b2(db)
    await hold(db, b_id, 100000, "REF-1")
    with pytest.raises(Conflict) as exc:
        await refund(db, b_id, 150000, "RFND-1")
    assert exc.value.code == "REFUND_EXCEEDS_ESCROW"

async def test_escrow_totals(db):
    b1, b2 = await get_b1_b2(db)
    await hold(db, b1, 100000, "H1")
    await release(db, b1, "R1")
    await hold(db, b2, 50000, "H2")
    await db.commit()
    released, held = await totals_for_bookings(db, [b1, b2])
    assert released == 100000
    assert held == 50000
