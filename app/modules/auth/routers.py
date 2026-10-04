from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.modules.user.models import User, Role
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "test_secret_key"
ALGORITHM = "HS256"

class RegisterRequest(BaseModel):
    email: str
    password: str
    role_name: str

@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).where(Role.name == req.role_name))
    role = result.scalars().first()
    if not role:
        role = Role(name=req.role_name)
        db.add(role)
        await db.flush()
    
    hashed_password = pwd_context.hash(req.password)
    user = User(email=req.email, password_hash=hashed_password, role_id=role.id)
    db.add(user)
    await db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    result_role = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result_role.scalars().first()
    role_name = role.name if role else "User"

    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": user.id, "role": role_name, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}
