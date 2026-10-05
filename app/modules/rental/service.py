from sqlalchemy.future import select
from app.core.errors import NotFound, Forbidden, Conflict
from app.modules.rental.models import Rental, RentalStaff
from app.core.config import get_settings

async def get_rental(db, rental_id: str) -> Rental:
    result = await db.execute(select(Rental).where(Rental.id == rental_id))
    rental = result.scalars().first()
    if not rental:
        raise NotFound("Rental tidak ditemukan")
    return rental

async def get_rental_id_for_staff(db, user_id: str) -> str | None:
    result = await db.execute(select(RentalStaff.rental_id).where(RentalStaff.user_id == user_id))
    return result.scalars().first()

async def assert_rental_staff(db, user_id: str, rental_id: str) -> None:
    staff_rental_id = await get_rental_id_for_staff(db, user_id)
    if not staff_rental_id or staff_rental_id != rental_id:
        raise Forbidden("Akses ditolak: bukan staf rental ini")

async def vehicle_limit(db, rental_id: str) -> int:
    # default for now
    settings = get_settings()
    return settings.default_max_vehicles

class RentalReadService:
    def __init__(self, db):
        self.db = db
        
    async def get_rental_status(self, rental_id: str) -> str:
        rental = await get_rental(self.db, rental_id)
        return rental.status_verifikasi

async def rental_ids_matching_location(db, lokasi: str) -> set[str]:
    result = await db.execute(
        select(Rental.id)
        .where(Rental.status_verifikasi == "LOLOS")
        .where(Rental.alamat.ilike(f"%{lokasi}%"))
    )
    return set(result.scalars().all())


from app.modules.payment.escrow import totals_for_bookings
from app.core.time import today_wib
from app.modules.rental.schemas import DashboardResponse

async def get_rental_dashboard(db, rental_id: str) -> DashboardResponse:
    from app.modules.booking.service import bookings_summary_for_rental
    today = today_wib()
    counts_by_state, booking_ids, upcoming = await bookings_summary_for_rental(db, rental_id, today)
    
    total_bookings = sum(counts_by_state.values())
    
    released, current_held = await totals_for_bookings(db, booking_ids)
    
    return DashboardResponse(
        total_bookings=total_bookings,
        bookings_by_state=counts_by_state,
        pendapatan_dicairkan=released,
        escrow_ditahan=current_held,
        upcoming_handovers=upcoming
    )
