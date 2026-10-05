from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.refund.models import Refund
from app.contracts.ports import RefundPort
from app.modules.payment import escrow
from app.modules.audit.service import AuditService

def calculate_refund_amount(paid_amount: int, tanggal_mulai: date, tanggal_batal: date) -> int:
    days = (tanggal_mulai - tanggal_batal).days
    if days >= 2:
        return paid_amount
    elif days == 1:
        return paid_amount // 2
    else:
        return 0

class RefundService(RefundPort):
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def trigger_refund(self, booking_id: str, amount: int, reason: str) -> str:
        if amount <= 0:
            return ""
            
        await escrow.refund(self.db, booking_id, amount, reason)
        
        refund = Refund(
            booking_id=booking_id,
            amount=amount,
            reason=reason
        )
        self.db.add(refund)
        await self.db.flush()
        
        await AuditService(self.db).log_event("REFUND_ISSUED", {"booking_id": booking_id, "amount": amount, "reason": reason})
        return refund.id
