import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.audit.models import AuditLog
from app.core.ids import new_id

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def log_event(self, event_name: str, payload: dict, actor_id: str | None = None) -> None:
        log = AuditLog(
            id=new_id(),
            event_name=event_name,
            payload=json.dumps(payload),
            actor_id=actor_id
        )
        self.db.add(log)
        # Note: caller commits
