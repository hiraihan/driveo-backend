from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notification.models import Notification
from app.core.ids import new_id

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def send(self, recipient: str, message: str, subject: str | None = None, channel: str = "EMAIL") -> None:
        notif = Notification(
            id=new_id(),
            type=channel,
            recipient=recipient,
            subject=subject,
            body=message,
            status="SENT"
        )
        self.db.add(notif)
        # Note: caller commits
