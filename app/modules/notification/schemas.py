from datetime import datetime
from pydantic import Field
from app.core.schemas import ResponseModel

class NotificationResponse(ResponseModel):
    id: str
    type: str
    recipient: str
    subject: str | None
    body: str
    status: str
    created_at: datetime
