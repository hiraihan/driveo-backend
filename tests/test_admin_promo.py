from app.modules.admin.models import MembershipPlan, Promo
import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select

async def test_promo_and_membership(client):
    from app.core.database import async_session
    from app.modules.admin.models import MembershipPlan, Promo
    from datetime import date, timedelta
    
    async with async_session() as session:
        m = MembershipPlan(name="Pro", price=100000, max_vehicles=20)
        session.add(m)
        
        p = Promo(code="DRIVE20", discount_percent=20.0, max_discount_amount=50000, valid_until=date.today() + timedelta(days=1))
        session.add(p)
        await session.commit()
        
        res = await session.execute(select(Promo).where(Promo.code == "DRIVE20"))
        promo = res.scalars().first()
        assert promo.max_discount_amount == 50000
