from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.vehicle.models import Vehicle
from app.modules.auth.dependencies import get_current_user, CurrentUser
from pydantic import BaseModel
from typing import List

router = APIRouter()

class VehicleCreate(BaseModel):
    rental_id: str
    jenis: str
    merk: str
    tipe: str
    plat_nomor: str
    tarif_dasar: float

class VehicleResponse(VehicleCreate):
    id: str
    status: str

@router.post("", response_model=VehicleResponse, status_code=201)
async def create_vehicle(req: VehicleCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in ["Admin", "Rental"]:
        raise HTTPException(status_code=403, detail="Not permitted")
    
    vehicle = Vehicle(**req.dict())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle

@router.get("", response_model=List[VehicleResponse])
async def list_vehicles(rental_id: str = None, db: AsyncSession = Depends(get_db)):
    query = select(Vehicle).where(Vehicle.is_deleted == False)
    if rental_id:
        query = query.where(Vehicle.rental_id == rental_id)
    
    result = await db.execute(query)
    vehicles = result.scalars().all()
    return vehicles
