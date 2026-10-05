from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.core.enums import UserRole
from app.core.errors import Conflict
from app.core.pagination import PageParams, Page, paginate
from app.core.ids import new_id
from app.core.time import utcnow
from app.modules.vehicle.models import Vehicle
from app.modules.vehicle.schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from app.modules.vehicle.service import get_vehicle, assert_vehicle_owner
from app.modules.rental.service import get_rental_id_for_staff, vehicle_limit

router = APIRouter(tags=["Vehicles"])

@router.post("", status_code=201, response_model=VehicleResponse)
async def create_vehicle(
    req: VehicleCreate,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    rental_id = await get_rental_id_for_staff(db, current_user.id)
    if not rental_id:
        raise Conflict("NO_RENTAL", "Anda bukan staf rental")
        
    v_limit = await vehicle_limit(db, rental_id)
    v_count = await db.scalar(
        select(func.count(Vehicle.id))
        .where(Vehicle.rental_id == rental_id)
        .where(Vehicle.is_deleted == False)
    )
    if v_count >= v_limit:
        raise Conflict("VEHICLE_LIMIT_REACHED", "Kuota kendaraan Anda sudah habis")
        
    v = Vehicle(
        id=new_id(),
        rental_id=rental_id,
        jenis=req.jenis,
        merk=req.merk,
        tipe=req.tipe,
        plat_nomor=req.plat_nomor,
        tarif_dasar=req.tarif_dasar
    )
    db.add(v)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise Conflict("PLATE_TAKEN", "Nomor plat sudah digunakan")
    await db.refresh(v)
    return v

@router.get("", response_model=Page[VehicleResponse])
async def list_vehicles(
    rental_id: str,
    params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Vehicle).where(Vehicle.rental_id == rental_id).where(Vehicle.is_deleted == False)
    return await paginate(db, stmt, params, VehicleResponse)

@router.get("/{id}", response_model=VehicleResponse)
async def get_vehicle_endpoint(id: str, db: AsyncSession = Depends(get_db)):
    return await get_vehicle(db, id)

@router.patch("/{id}", response_model=VehicleResponse)
async def update_vehicle(
    id: str,
    req: VehicleUpdate,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    v = await assert_vehicle_owner(db, current_user.id, id)
    
    if req.jenis is not None: v.jenis = req.jenis
    if req.merk is not None: v.merk = req.merk
    if req.tipe is not None: v.tipe = req.tipe
    if req.plat_nomor is not None: v.plat_nomor = req.plat_nomor
    if req.tarif_dasar is not None: v.tarif_dasar = req.tarif_dasar
    if req.status is not None: v.status = req.status.value
    v.updated_at = utcnow()
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise Conflict("PLATE_TAKEN", "Nomor plat sudah digunakan")
        
    await db.refresh(v)
    return v

@router.delete("/{id}", status_code=204)
async def delete_vehicle(
    id: str,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    v = await assert_vehicle_owner(db, current_user.id, id)
    v.is_deleted = True
    v.updated_at = utcnow()
    await db.commit()
