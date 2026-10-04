from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.listing.models import Listing
from typing import List

router = APIRouter()

@router.get("", summary="Search and compare listings")
async def search_vehicles(q: str = "", min_price: float = 0, max_price: float = 999999999, db: AsyncSession = Depends(get_db)):
    query = select(Listing).where(Listing.status_publikasi == "PUBLISHED")
    query = query.where(Listing.harga_all_in >= min_price).where(Listing.harga_all_in <= max_price)
    
    if q:
        query = query.where(Listing.judul.ilike(f"%{q}%"))
        
    result = await db.execute(query)
    return result.scalars().all()
