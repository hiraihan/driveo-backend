from datetime import datetime
from sqlalchemy.future import select
from app.core.config import get_settings
from app.core.errors import NotFound
from app.core.enums import ListingStatus
from app.modules.listing.models import Listing

def compute_all_in(tarif_dasar: int, biaya_tambahan: int) -> int:
    return tarif_dasar + biaya_tambahan

def is_stale(updated_at: datetime, now: datetime) -> bool:
    settings = get_settings()
    if updated_at.tzinfo is None:
        from datetime import timezone
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    delta = now - updated_at
    return delta.days > settings.listing_stale_days

async def get_published_listing(db, listing_id: str) -> Listing:
    result = await db.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .where(Listing.status_publikasi == ListingStatus.PUBLISHED.value)
    )
    listing = result.scalars().first()
    if not listing:
        raise NotFound("Listing tidak ditemukan atau belum dipublikasikan")
    return listing
