from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.listing.models import Listing
from app.modules.auth.dependencies import get_current_user, CurrentUser
from pydantic import BaseModel
from typing import List

router = APIRouter()

class ListingCreate(BaseModel):
    vehicle_id: str
    judul: str
    deskripsi: str
    harga_all_in: float

class ListingResponse(ListingCreate):
    id: str
    status_publikasi: str

@router.post("", response_model=ListingResponse, status_code=201)
async def create_listing(req: ListingCreate, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    listing = Listing(**req.dict())
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing

@router.get("", response_model=List[ListingResponse])
async def get_listings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Listing).where(Listing.status_publikasi == "PUBLISHED"))
    return result.scalars().all()
