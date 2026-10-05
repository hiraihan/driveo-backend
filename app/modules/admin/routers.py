from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.errors import Conflict
from app.core.enums import UserRole
from app.modules.auth.dependencies import get_current_user, CurrentUser, require_roles
from app.modules.admin.models import Promo, MembershipPlan
from app.modules.admin.schemas import PromoCreate, PromoResponse, MembershipCreate, MembershipResponse
from app.core.pagination import PageParams, Page, paginate
from app.modules.audit.service import AuditService

router = APIRouter()

@router.post("/promos", status_code=201, response_model=PromoResponse)
async def create_promo(req: PromoCreate, current_user: CurrentUser = Depends(require_roles(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promo).where(Promo.code == req.code))
    if result.scalars().first():
        raise Conflict("PROMO_CODE_TAKEN", "Kode promo sudah ada")
        
    from app.core.ids import new_id
    promo = Promo(id=new_id(), code=req.code, discount_percent=req.discount_percent, max_discount_amount=req.max_discount_amount, valid_until=req.valid_until)
    db.add(promo)
    await AuditService(db).log_event("PROMO_CREATED", {"code": promo.code}, actor_id=current_user.id)
    await db.commit()
    await db.refresh(promo)
    return promo

@router.get("/promos", response_model=Page[PromoResponse])
async def list_promos(params: PageParams = Depends(), current_user: CurrentUser = Depends(require_roles(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    return await paginate(db, select(Promo), params, PromoResponse)

@router.post("/memberships", status_code=201, response_model=MembershipResponse)
async def create_membership(req: MembershipCreate, current_user: CurrentUser = Depends(require_roles(UserRole.ADMIN)), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan).where(MembershipPlan.name == req.name))
    if result.scalars().first():
        raise Conflict("MEMBERSHIP_NAME_TAKEN", "Nama membership sudah ada")
        
    from app.core.ids import new_id
    plan = MembershipPlan(id=new_id(), name=req.name, price=req.price, max_vehicles=req.max_vehicles, max_staff=req.max_staff)
    db.add(plan)
    await AuditService(db).log_event("MEMBERSHIP_CREATED", {"name": plan.name}, actor_id=current_user.id)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.get("/memberships", response_model=list[MembershipResponse])
async def list_memberships(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan))
    plans = result.scalars().all()
    return [MembershipResponse.model_validate(p) for p in plans]
