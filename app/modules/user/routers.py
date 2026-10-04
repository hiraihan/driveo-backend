from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.user.models import User, UserConsent
from app.modules.auth.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ConsentRequest(BaseModel):
    document_type: str
    version: str

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "role_id": user.role_id, "is_active": user.is_active}

@router.post("/me/consents", status_code=201)
async def record_consent(req: ConsentRequest, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    consent = UserConsent(user_id=current_user["sub"], document_type=req.document_type, version=req.version)
    db.add(consent)
    await db.commit()
    return {"message": "Consent recorded"}
