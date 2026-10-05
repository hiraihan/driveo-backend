from app.modules.user.models import User
from app.core.enums import UserRole
from app.modules.auth.security import hash_password, create_access_token
from app.modules.user.service import get_or_create_role
from app.core.ids import new_id

async def make_user(db, role: UserRole = UserRole.PENYEWA, email: str | None = None, is_active: bool = True) -> User:
    email = email or f"user_{new_id()}@example.com"
    r = await get_or_create_role(db, role)
    u = User(email=email, password_hash=hash_password("password"), role_id=r.id, is_active=is_active)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u

async def make_admin(db, email: str | None = None) -> User:
    return await make_user(db, role=UserRole.ADMIN, email=email)

def auth_header(user: User, role: UserRole | None = None) -> dict:
    token = create_access_token(user.id, role or UserRole.PENYEWA)
    return {"Authorization": f"Bearer {token}"}

from app.modules.rental.models import Rental, RentalStaff
from app.core.enums import RentalStatus

async def make_rental(db, owner: User, status: RentalStatus = RentalStatus.LOLOS) -> Rental:
    from app.core.ids import new_id
    r = Rental(
        id=new_id(),
        nama_usaha=f"Rental {new_id()[:5]}",
        nib="1234567890",
        alamat="Jl. Test",
        kontak="0812345678",
        status_verifikasi=status,
        payout_account="ENCRYPTED_123"
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    
    staff = RentalStaff(id=new_id(), rental_id=r.id, user_id=owner.id, is_owner=True)
    db.add(staff)
    await db.commit()
    
    # Also update user role to RENTAL
    r_role = await get_or_create_role(db, UserRole.RENTAL)
    owner.role_id = r_role.id
    db.add(owner)
    await db.commit()
    
    return r

from app.modules.vehicle.models import Vehicle
from app.core.enums import VehicleStatus

async def make_vehicle(db, rental, **kw) -> Vehicle:
    from app.core.ids import new_id
    v = Vehicle(
        id=new_id(),
        rental_id=rental.id,
        jenis=kw.get("jenis", "Mobil"),
        merk=kw.get("merk", "Toyota"),
        tipe=kw.get("tipe", "Avanza"),
        plat_nomor=kw.get("plat_nomor", f"B {new_id()[:8].upper()} {new_id()[-4:].upper()}"),
        tarif_dasar=kw.get("tarif_dasar", 300000),
        status=kw.get("status", VehicleStatus.AKTIF.value)
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v

from app.modules.listing.models import Listing
from app.core.enums import ListingStatus

async def make_listing(db, vehicle, status: ListingStatus = ListingStatus.PUBLISHED, biaya_tambahan: int = 0) -> Listing:
    from app.core.ids import new_id
    l = Listing(
        id=new_id(),
        vehicle_id=vehicle.id,
        rental_id=vehicle.rental_id,
        judul=f"Sewa {vehicle.merk} {vehicle.tipe}",
        deskripsi="Mobil bagus",
        biaya_tambahan=biaya_tambahan,
        harga_all_in=vehicle.tarif_dasar + biaya_tambahan,
        status_publikasi=status.value
    )
    db.add(l)
    await db.commit()
    await db.refresh(l)
    return l
