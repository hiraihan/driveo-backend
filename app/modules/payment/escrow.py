from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.modules.payment.models import EscrowLedger
from app.core.enums import LedgerEntryType, EscrowState
from app.core.errors import Conflict
from app.contracts.ports import EscrowReadPort
from app.modules.booking.service import get_booking

async def hold(db: AsyncSession, booking_id: str, amount: int, reference: str) -> None:
    if amount <= 0:
        raise ValueError("Amount must be > 0")
    db.add(EscrowLedger(
        booking_id=booking_id,
        entry_type=LedgerEntryType.HOLD,
        amount=amount,
        reference=reference
    ))

async def balance(db: AsyncSession, booking_id: str) -> int:
    stmt = select(EscrowLedger.entry_type, func.sum(EscrowLedger.amount)).where(
        EscrowLedger.booking_id == booking_id
    ).group_by(EscrowLedger.entry_type)
    
    result = await db.execute(stmt)
    totals = dict(result.all())
    
    holds = totals.get(LedgerEntryType.HOLD, 0)
    releases = totals.get(LedgerEntryType.RELEASE, 0)
    refunds = totals.get(LedgerEntryType.REFUND, 0)
    
    return holds - releases - refunds

async def release(db: AsyncSession, booking_id: str, reference: str) -> int:
    current_balance = await balance(db, booking_id)
    if current_balance <= 0:
        return 0
        
    db.add(EscrowLedger(
        booking_id=booking_id,
        entry_type=LedgerEntryType.RELEASE,
        amount=current_balance,
        reference=reference
    ))
    return current_balance

async def refund(db: AsyncSession, booking_id: str, amount: int, reference: str) -> None:
    if amount <= 0:
        raise ValueError("Amount must be > 0")
    current_balance = await balance(db, booking_id)
    if amount > current_balance:
        raise Conflict("REFUND_EXCEEDS_ESCROW", "Refund amount exceeds current escrow balance")
        
    db.add(EscrowLedger(
        booking_id=booking_id,
        entry_type=LedgerEntryType.REFUND,
        amount=amount,
        reference=reference
    ))

async def totals_for_bookings(db: AsyncSession, booking_ids: list[str]) -> tuple[int, int]:
    if not booking_ids:
        return 0, 0
    stmt = select(EscrowLedger.entry_type, func.sum(EscrowLedger.amount)).where(
        EscrowLedger.booking_id.in_(booking_ids)
    ).group_by(EscrowLedger.entry_type)
    result = await db.execute(stmt)
    totals = dict(result.all())
    
    held = totals.get(LedgerEntryType.HOLD, 0)
    released = totals.get(LedgerEntryType.RELEASE, 0)
    refunded = totals.get(LedgerEntryType.REFUND, 0)
    
    current_held = held - released - refunded
    return released, current_held

class EscrowReadService(EscrowReadPort):
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_state(self, booking_id: str) -> EscrowState:
        booking = await get_booking(self.db, booking_id)
        return booking.escrow_state
