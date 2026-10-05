from app.modules.verification.models import Verification
from app.modules.audit.models import AuditLog
import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select

async def test_verification_and_audit():
    from app.core.database import async_session
    from app.modules.verification.models import Verification
    from app.modules.audit.models import AuditLog
    
    async with async_session() as session:
        v = Verification(user_id="user_b", status="LOLOS", data_ektp="mock_data")
        session.add(v)
        
        a = AuditLog(event_name="VERIFICATION_SUBMITTED", payload='{"user": "user_b"}')
        session.add(a)
        
        await session.commit()
        
        result_v = await session.execute(select(Verification).where(Verification.user_id == "user_b"))
        assert result_v.scalars().first().status == "LOLOS"
        
        result_a = await session.execute(select(AuditLog).where(AuditLog.event_name == "VERIFICATION_SUBMITTED"))
        assert result_a.scalars().first() is not None
