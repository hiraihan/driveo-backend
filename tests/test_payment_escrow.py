from app.modules.payment.models import Payment, EscrowLedger
import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio(loop_scope="function")
async def test_payment_and_escrow():
    from app.core.database import async_session
    from app.modules.payment.models import Payment
    from app.modules.payment.models import EscrowLedger
    
    async with async_session() as session:
        p = Payment(booking_id="b_123", amount=450000, status="BERHASIL", external_id="midtrans_123")
        session.add(p)
        
        e = EscrowLedger(booking_id="b_123", amount=450000, status="DITAHAN")
        session.add(e)
        
        await session.commit()
        
        res = await session.execute(select(EscrowLedger).where(EscrowLedger.booking_id == "b_123"))
        assert res.scalars().first().status == "DITAHAN"
