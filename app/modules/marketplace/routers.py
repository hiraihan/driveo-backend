from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.core.database import get_db
from app.core.errors import NotFound
from app.modules.marketplace import models as m
from app.modules.marketplace import schemas as s

router = APIRouter(tags=["Marketplace"])


@router.get("/pickup-spots", response_model=list[s.PickupSpotResponse])
async def list_pickup_spots(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.PickupSpot).order_by(m.PickupSpot.extra_fee))
    rows = result.scalars().all()
    return [s.PickupSpotResponse.from_row(r) for r in rows]


@router.get("/vehicles", response_model=list[s.VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.MarketplaceVehicle))
    rows = result.scalars().all()
    return [s.VehicleResponse.from_row(r) for r in rows]


@router.get("/vehicles/{id}", response_model=s.VehicleResponse)
async def get_vehicle(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.MarketplaceVehicle).where(m.MarketplaceVehicle.id == id))
    row = result.scalars().first()
    if not row:
        raise NotFound("Kendaraan tidak ditemukan")
    return s.VehicleResponse.from_row(row)


@router.get("/vehicles/by-rental/{rental_id}", response_model=list[s.VehicleResponse])
async def list_vehicles_by_rental(rental_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(m.MarketplaceVehicle).where(m.MarketplaceVehicle.rental_id == rental_id)
    )
    rows = result.scalars().all()
    return [s.VehicleResponse.from_row(r) for r in rows]


@router.get("/rentals", response_model=list[s.RentalResponse])
async def list_rentals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.MarketplaceRental))
    rows = result.scalars().all()
    return [s.RentalResponse.from_row(r) for r in rows]


@router.get("/rentals/{id}", response_model=s.RentalResponse)
async def get_rental(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.MarketplaceRental).where(m.MarketplaceRental.id == id))
    row = result.scalars().first()
    if not row:
        raise NotFound("Mitra rental tidak ditemukan")
    return s.RentalResponse.from_row(row)


@router.get("/listings", response_model=list[s.ListingResponse])
async def list_listings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.MarketplaceListing))
    rows = result.scalars().all()
    return [s.ListingResponse.from_row(r) for r in rows]


@router.get("/disputes", response_model=list[s.DisputeResponse])
async def list_disputes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.Dispute))
    rows = result.scalars().all()
    return [s.DisputeResponse.from_row(r) for r in rows]


@router.get("/disputes/{id}", response_model=s.DisputeResponse)
async def get_dispute(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(m.Dispute).where(or_(m.Dispute.id == id, m.Dispute.ticket_code == id))
    )
    row = result.scalars().first()
    if not row:
        raise NotFound("Sengketa tidak ditemukan")
    return s.DisputeResponse.from_row(row)


@router.get("/notifications", response_model=list[s.NotificationResponse])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(m.InAppNotification).order_by(m.InAppNotification.timestamp.desc()))
    rows = result.scalars().all()
    return [s.NotificationResponse.from_row(r) for r in rows]