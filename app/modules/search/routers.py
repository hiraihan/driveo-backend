from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, asc
from app.core.database import get_db
from app.models import Listing, Vehicle, Rental
from app.modules.search.schemas import SearchParams
from app.modules.availability.service import blocked_vehicle_ids
from app.modules.vehicle.service import vehicle_ids_by_jenis

router = APIRouter()

@router.get("", summary="Search and compare listings")
async def search_vehicles(params: SearchParams = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(Listing).where(Listing.status_publikasi == "PUBLISHED")
    
    if params.min_price is not None:
        query = query.where(Listing.harga_all_in >= params.min_price)
    if params.max_price is not None:
        query = query.where(Listing.harga_all_in <= params.max_price)
    
    if params.q:
        query = query.where(Listing.judul.ilike(f"%{params.q}%"))
        
    if params.start_date and params.end_date:
        blocked_ids = await blocked_vehicle_ids(db, params.start_date, params.end_date)
        if blocked_ids:
            query = query.where(Listing.vehicle_id.notin_(blocked_ids))
            
    if params.jenis:
        jenis_ids = await vehicle_ids_by_jenis(db, params.jenis)
        if jenis_ids:
            query = query.where(Listing.vehicle_id.in_(jenis_ids))
        else:
            query = query.where(False)
            
    if params.lokasi:
        query = query.join(Vehicle, Listing.vehicle_id == Vehicle.id).join(Rental, Vehicle.rental_id == Rental.id).where(Rental.alamat.ilike(f"%{params.lokasi}%"))

    if params.sort == "price_asc":
        query = query.order_by(asc(Listing.harga_all_in))
    elif params.sort == "price_desc":
        query = query.order_by(desc(Listing.harga_all_in))
    else:
        query = query.order_by(desc(Listing.updated_at))
        
    count_query = select(func.count()).select_from(query.subquery())
    total_items = await db.scalar(count_query)
    
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    result = await db.execute(query)
    data = result.scalars().all()
    
    return {
        "data": data,
        "pagination": {
            "page": params.page,
            "page_size": params.page_size,
            "total_items": total_items
        }
    }
