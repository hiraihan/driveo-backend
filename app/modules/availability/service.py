from datetime import date, timedelta
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete
from app.core.errors import Conflict
from app.core.ids import new_id
from app.core.enums import SlotStatus
from app.modules.availability.models import VehicleAvailability

async def lock_slots(db, vehicle_id: str, start: date, end: date, booking_id: str) -> None:
    current = start
    async with db.begin_nested():
        while current <= end:
            slot = VehicleAvailability(
                id=new_id(),
                vehicle_id=vehicle_id,
                tanggal=current,
                status=SlotStatus.DIPESAN.value,
                booking_id=booking_id
            )
            db.add(slot)
            current += timedelta(days=1)
        try:
            await db.flush()
        except IntegrityError:
            raise Conflict("SLOT_UNAVAILABLE", "Kendaraan tidak tersedia pada tanggal tersebut")

async def release_slots(db, booking_id: str) -> int:
    stmt = delete(VehicleAvailability).where(VehicleAvailability.booking_id == booking_id)
    result = await db.execute(stmt)
    return result.rowcount

async def block_dates(db, vehicle_id: str, dates: list[date]) -> None:
    async with db.begin_nested():
        for d in dates:
            slot = VehicleAvailability(
                id=new_id(),
                vehicle_id=vehicle_id,
                tanggal=d,
                status=SlotStatus.DIBLOKIR.value
            )
            db.add(slot)
        try:
            await db.flush()
        except IntegrityError:
            raise Conflict("SLOT_UNAVAILABLE", "Kendaraan tidak tersedia pada tanggal tersebut")

async def unblock_date(db, vehicle_id: str, tanggal: date) -> None:
    result = await db.execute(
        select(VehicleAvailability)
        .where(VehicleAvailability.vehicle_id == vehicle_id)
        .where(VehicleAvailability.tanggal == tanggal)
    )
    slot = result.scalars().first()
    if not slot:
        return
    if slot.status == SlotStatus.DIPESAN.value:
        raise Conflict("SLOT_BOOKED", "Tidak dapat menghapus blokir karena tanggal ini sudah dipesan")
    await db.delete(slot)

async def blocked_vehicle_ids(db, start: date, end: date) -> set[str]:
    result = await db.execute(
        select(VehicleAvailability.vehicle_id)
        .where(VehicleAvailability.tanggal >= start)
        .where(VehicleAvailability.tanggal <= end)
    )
    return set(result.scalars().all())
