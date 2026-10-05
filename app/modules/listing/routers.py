from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.core.enums import UserRole, ListingStatus, RentalStatus, VehicleStatus
from app.core.errors import Conflict, NotFound, Forbidden
from app.core.ids import new_id
from app.core.time import utcnow
from app.modules.listing.models import Listing
from app.modules.listing.schemas import ListingCreate, ListingUpdate, ListingResponse
from app.modules.listing.service import compute_all_in, is_stale, get_published_listing
from app.modules.vehicle.service import assert_vehicle_owner
from app.modules.rental.service import get_rental

router = APIRouter(tags=["Listings"])

def _to_response(listing: Listing) -> ListingResponse:
    # Build schema explicitly since is_stale is computed
    return ListingResponse(
        id=listing.id,
        vehicle_id=listing.vehicle_id,
        rental_id=listing.rental_id,
        judul=listing.judul,
        deskripsi=listing.deskripsi,
        harga_all_in=listing.harga_all_in,
        status_publikasi=ListingStatus(listing.status_publikasi),
        updated_at=listing.updated_at,
        is_stale=is_stale(listing.updated_at, utcnow())
    )

@router.post("", status_code=201, response_model=ListingResponse)
async def create_listing(
    req: ListingCreate,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    v = await assert_vehicle_owner(db, current_user.id, req.vehicle_id)
    
    listing = Listing(
        id=new_id(),
        vehicle_id=v.id,
        rental_id=v.rental_id,
        judul=req.judul,
        deskripsi=req.deskripsi,
        biaya_tambahan=req.biaya_tambahan,
        harga_all_in=compute_all_in(v.tarif_dasar, req.biaya_tambahan),
        status_publikasi=ListingStatus.DRAFT.value
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return _to_response(listing)

@router.patch("/{id}", response_model=ListingResponse)
async def update_listing(
    id: str,
    req: ListingUpdate,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    listing = (await db.execute(select(Listing).where(Listing.id == id))).scalars().first()
    if not listing:
        raise NotFound("Listing tidak ditemukan")
        
    v = await assert_vehicle_owner(db, current_user.id, listing.vehicle_id)
    
    if req.judul is not None: listing.judul = req.judul
    if req.deskripsi is not None: listing.deskripsi = req.deskripsi
    if req.biaya_tambahan is not None:
        listing.biaya_tambahan = req.biaya_tambahan
        listing.harga_all_in = compute_all_in(v.tarif_dasar, req.biaya_tambahan)
        
    listing.updated_at = utcnow()
    await db.commit()
    await db.refresh(listing)
    return _to_response(listing)

@router.post("/{id}/publish", response_model=ListingResponse)
async def publish_listing(
    id: str,
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    listing = (await db.execute(select(Listing).where(Listing.id == id))).scalars().first()
    if not listing:
        raise NotFound("Listing tidak ditemukan")
        
    v = await assert_vehicle_owner(db, current_user.id, listing.vehicle_id)
    rental = await get_rental(db, listing.rental_id)
    
    if rental.status_verifikasi != RentalStatus.LOLOS.value:
        raise Conflict("RENTAL_NOT_VERIFIED", "Rental belum diverifikasi")
    if v.status != VehicleStatus.AKTIF.value:
        raise Conflict("VEHICLE_INACTIVE", "Kendaraan tidak aktif")
        
    listing.status_publikasi = ListingStatus.PUBLISHED.value
    listing.updated_at = utcnow()
    await db.commit()
    await db.refresh(listing)
    return _to_response(listing)

@router.get("/{id}", response_model=ListingResponse)
async def get_listing_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    listing = await get_published_listing(db, id)
    return _to_response(listing)
