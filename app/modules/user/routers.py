from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.user.models import User, UserConsent
from app.modules.auth.dependencies import get_current_user, CurrentUser
from pydantic import BaseModel
from app.modules.auth.schemas import UserResponse

router = APIRouter()

class ConsentRequest(BaseModel):
    document_type: str
    version: str

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user.id, email=user.email, role=current_user.role.value,
                        name=user.name, phone=user.phone)

@router.post("/me/consents", status_code=201)
async def record_consent(req: ConsentRequest, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.core.ids import new_id
    consent = UserConsent(id=new_id(), user_id=current_user.id, document_type=req.document_type, version=req.version)
    db.add(consent)
    await db.commit()
    return {"message": "Consent recorded"}
