from app.modules.vehicle.models import Vehicle, VehicleAvailability
from app.modules.listing.models import Listing
import pytest
import pytest_asyncio
from app.core.database import Base, engine
from app.modules.vehicle.models import Vehicle, VehicleAvailability
from sqlalchemy.future import select
from datetime import date
import uuid

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio(loop_scope="function")
async def test_vehicle_models_and_availability():
    from app.core.database import async_session
    
    rental_id = str(uuid.uuid4())
    async with async_session() as session:
        v = Vehicle(rental_id=rental_id, jenis="Mobil", merk="Toyota", tipe="Avanza", plat_nomor="B1234XYZ", tarif_dasar=500000)
        session.add(v)
        await session.commit()
        
        # Test availability
        avail = VehicleAvailability(vehicle_id=v.id, tanggal=date(2026, 12, 1), status="tersedia")
        session.add(avail)
        await session.commit()
        
        result = await session.execute(select(VehicleAvailability).where(VehicleAvailability.vehicle_id == v.id))
        a = result.scalars().first()
        assert a.status == "tersedia"

@pytest.mark.asyncio(loop_scope="function")
async def test_listing_model():
    from app.core.database import async_session
    from app.modules.listing.models import Listing
    
    async with async_session() as session:
        l = Listing(vehicle_id="test_v", judul="Avanza Murah", harga_all_in=600000, skor_kebasuan=0)
        session.add(l)
        await session.commit()
        
        result = await session.execute(select(Listing).where(Listing.vehicle_id == "test_v"))
        listing = result.scalars().first()
        assert listing.harga_all_in == 600000
