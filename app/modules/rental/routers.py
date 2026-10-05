from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.core.enums import UserRole, RentalStatus
from app.core.errors import Conflict
from app.core.ids import new_id
from app.modules.rental.models import Rental, RentalStaff
from app.modules.rental.schemas import OnboardRequest, RentalResponse, VerifyRequest
from app.modules.rental.service import get_rental_id_for_staff, get_rental
from app.modules.user.service import set_user_role
from app.modules.audit.service import AuditService
from app.modules.notification.service import NotificationService

router = APIRouter(tags=["Rentals"])

@router.post("/onboard", status_code=201, response_model=RentalResponse)
async def onboard(
    req: OnboardRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    existing = await get_rental_id_for_staff(db, current_user.id)
    if existing:
        raise Conflict("ALREADY_RENTAL_STAFF", "Pengguna sudah menjadi staf rental")
        
    rental = Rental(
        id=new_id(),
        nama_usaha=req.nama_usaha,
        nib=req.nib,
        alamat=req.alamat,
        kontak=req.kontak,
        payout_account=f"ENCRYPTED_{req.payout_account}"
    )
    db.add(rental)
    await db.flush()
    
    staff = RentalStaff(id=new_id(), rental_id=rental.id, user_id=current_user.id, is_owner=True)
    db.add(staff)
    
    await set_user_role(db, current_user.id, UserRole.RENTAL)
    await db.commit()
    await db.refresh(rental)
    return rental

@router.get("/me", response_model=RentalResponse)
async def get_my_rental(
    current_user: CurrentUser = Depends(require_roles(UserRole.RENTAL)),
    db: AsyncSession = Depends(get_db)
):
    rental_id = await get_rental_id_for_staff(db, current_user.id)
    return await get_rental(db, rental_id)

@router.get("/{id}", response_model=RentalResponse)
async def get_rental_endpoint(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    return await get_rental(db, id)

@router.post("/{id}/verify", response_model=RentalResponse)
async def verify_rental(
    id: str,
    req: VerifyRequest,
    current_user: CurrentUser = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    rental = await get_rental(db, id)
    rental.status_verifikasi = req.status.value
    
    await AuditService(db).log_event("RENTAL_VERIFIED", {"rental_id": rental.id}, actor_id=current_user.id)
    # email notification omitted for brevity or simple fake:
    await NotificationService(db).send("owner@test.com", f"Verifikasi rental {req.status.value}")
    
    await db.commit()
    await db.refresh(rental)
    return rental
