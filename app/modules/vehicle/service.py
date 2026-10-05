from sqlalchemy.future import select
from app.core.errors import NotFound, Forbidden
from app.modules.vehicle.models import Vehicle
from app.modules.rental.service import get_rental_id_for_staff

async def get_vehicle(db, vehicle_id: str) -> Vehicle:
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id).where(Vehicle.is_deleted == False)
    )
    v = result.scalars().first()
    if not v:
        raise NotFound("Kendaraan tidak ditemukan")
    return v

async def assert_vehicle_owner(db, user_id: str, vehicle_id: str) -> Vehicle:
    v = await get_vehicle(db, vehicle_id)
    rental_id = await get_rental_id_for_staff(db, user_id)
    if not rental_id or v.rental_id != rental_id:
        raise Forbidden("Akses ditolak: Anda bukan pemilik kendaraan ini")
    return v

async def vehicle_ids_by_jenis(db, jenis: str) -> set[str]:
    result = await db.execute(
        select(Vehicle.id).where(Vehicle.jenis.ilike(f"%{jenis}%")).where(Vehicle.is_deleted == False)
    )
    return set(result.scalars().all())
