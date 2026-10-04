from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notification.models import Notification
from app.contracts.ports import NotificationPort

class NotificationService(NotificationPort):
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def send_email(self, recipient: str, subject: str, body: str):
        # Mock actual sending
        notif = Notification(type="EMAIL", recipient=recipient, subject=subject, body=body, status="SENT")
        self.db.add(notif)
        await self.db.commit()
        
    def send(self, recipient: str, message: str) -> None:
        pass # Implementation for sync port interface if needed, or update port to async
