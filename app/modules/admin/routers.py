from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.admin.models import MembershipPlan, Promo
from app.modules.auth.dependencies import get_current_user, depends_on_role
from pydantic import BaseModel
from datetime import date
from typing import List

router = APIRouter()

class MembershipCreate(BaseModel):
    name: str
    price: float
    max_vehicles: int
    max_staff: int

@router.post("/memberships", status_code=201)
async def create_membership(req: MembershipCreate, current_user: dict = Depends(depends_on_role("Admin")), db: AsyncSession = Depends(get_db)):
    plan = MembershipPlan(**req.dict())
    db.add(plan)
    await db.commit()
    return plan

@router.get("/memberships")
async def get_memberships(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MembershipPlan))
    return result.scalars().all()

class PromoCreate(BaseModel):
    code: str
    discount_percent: float
    max_discount_amount: float
    valid_until: date

@router.post("/promos", status_code=201)
async def create_promo(req: PromoCreate, current_user: dict = Depends(depends_on_role("Admin")), db: AsyncSession = Depends(get_db)):
    promo = Promo(**req.dict())
    db.add(promo)
    await db.commit()
    return promo

@router.get("/promos")
async def get_promos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Promo))
    return result.scalars().all()
