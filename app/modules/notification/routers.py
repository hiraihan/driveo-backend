from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, require_roles, CurrentUser
from app.core.enums import UserRole
from app.modules.notification.models import Notification
from app.modules.notification.schemas import NotificationResponse

router = APIRouter(tags=["Notifications"])

@router.get("/me", response_model=list[NotificationResponse])
async def get_my_notifications(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.recipient == user.email)
        .order_by(desc(Notification.created_at))
    )
    return result.scalars().all()

@router.get("", response_model=list[NotificationResponse])
async def get_all_notifications(
    admin: CurrentUser = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .order_by(desc(Notification.created_at))
    )
    return result.scalars().all()
