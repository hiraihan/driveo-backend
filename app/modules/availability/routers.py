from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.core.enums import UserRole
from app.modules.availability.models import VehicleAvailability
from app.modules.availability.schemas import BlockRequest, SlotResponse
from app.modules.availability.service import block_dates, unblock_date
from app.modules.vehicle.service import assert_vehicle_owner

router = APIRouter(tags=["Availability"])

@router.get("/vehicles/{vehicle_id}/availability", response_model=list[SlotResponse])
async def get_availability(
    vehicle_id: str,
    start: date,
    end: date,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    await assert_vehicle_owner(db, current_user.id, vehicle_id)
    result = await db.execute(
        select(VehicleAvailability)
        .where(VehicleAvailability.vehicle_id == vehicle_id)
        .where(VehicleAvailability.tanggal >= start)
        .where(VehicleAvailability.tanggal <= end)
        .order_by(VehicleAvailability.tanggal)
    )
    return result.scalars().all()

@router.post("/vehicles/{vehicle_id}/blocks", status_code=201)
async def block_vehicle_dates(
    vehicle_id: str,
    req: BlockRequest,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    await assert_vehicle_owner(db, current_user.id, vehicle_id)
    await block_dates(db, vehicle_id, req.dates)
    await db.commit()
    return {"status": "ok"}

@router.delete("/vehicles/{vehicle_id}/blocks/{tanggal}", status_code=204)
async def unblock_vehicle_date(
    vehicle_id: str,
    tanggal: date,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    await assert_vehicle_owner(db, current_user.id, vehicle_id)
    await unblock_date(db, vehicle_id, tanggal)
    await db.commit()
