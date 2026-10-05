import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select
from app.modules.notification.models import Notification
from app.modules.notification.service import NotificationService

async def test_notification_service():
    from app.core.database import async_session
    async with async_session() as session:
        service = NotificationService(session)
        await service.send_email("user@example.com", "Test", "Test body")
        
        result = await session.execute(select(Notification).where(Notification.recipient == "user@example.com"))
        notif = result.scalars().first()
        assert notif is not None
        assert notif.status == "SENT"
