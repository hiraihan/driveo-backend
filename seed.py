import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session, engine, Base
from app.modules.user.models import User, Role
from app.modules.auth.routers import pwd_context
from app.modules.rental.models import Rental, RentalStaff
from app.modules.admin.models import MembershipPlan, Promo
from app.modules.vehicle.models import Vehicle
from app.modules.listing.models import Listing
from datetime import date, timedelta

async def seed_data():
    print("Seeding database for competition...")
    async with async_session() as session:
        # Create Users (Admin, Rental, Customer)
        
        role_admin = Role(name="Admin")
        role_rental = Role(name="Rental")
        role_cust = Role(name="Penyewa")
        session.add_all([role_admin, role_rental, role_cust])
        await session.flush()

        admin = User(email="admin@driveo.com", password_hash=pwd_context.hash("admin123"), role_id=role_admin.id)
        rental_owner = User(email="rental@driveo.com", password_hash=pwd_context.hash("rental123"), role_id=role_rental.id)
        customer = User(email="customer@driveo.com", password_hash=pwd_context.hash("customer123"), role_id=role_cust.id)

        
        session.add_all([admin, rental_owner, customer])
        await session.flush()

        # Create Memberships
        plan_basic = MembershipPlan(name="Basic", price=0.0, max_vehicles=5, max_staff=1)
        plan_pro = MembershipPlan(name="Pro", price=150000.0, max_vehicles=20, max_staff=5)
        
        # Create Promo
        promo = Promo(code="LOMBA26", discount_percent=50.0, max_discount_amount=100000.0, valid_until=date.today() + timedelta(days=30))
        
        session.add_all([plan_basic, plan_pro, promo])
        await session.flush()
        
        # Create Rental Profile
        rental = Rental(nama_usaha="DriveO Official Rental", nib="123456789", alamat="Jl. Lomba No 1", kontak="08123", status_verifikasi="LOLOS", membership_id=plan_pro.id)
        session.add(rental)
        await session.flush()
        
        staff = RentalStaff(rental_id=rental.id, user_id=rental_owner.id, role="Admin")
        session.add(staff)
        
        # Create Vehicle
        vehicle = Vehicle(rental_id=rental.id, jenis="Mobil", merk="Toyota", tipe="Avanza", plat_nomor="B 1234 LOMBA", tarif_dasar=300000.0)
        session.add(vehicle)
        await session.flush()
        
        # Create Listing
        listing = Listing(vehicle_id=vehicle.id, judul="Avanza Siap Lomba", deskripsi="Kondisi prima untuk Demo", harga_all_in=350000.0, status_publikasi="PUBLISHED")
        session.add(listing)
        
        await session.commit()
    print("Seed complete! You can login with admin@driveo.com / admin123")

if __name__ == "__main__":
    asyncio.run(seed_data())
