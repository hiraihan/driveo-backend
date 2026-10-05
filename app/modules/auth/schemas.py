from pydantic import EmailStr, Field
from app.core.schemas import RequestModel, ResponseModel
from app.core.enums import UserRole

class RegisterRequest(RequestModel):
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(ResponseModel):
    id: str
    email: str
    role: str

class TokenResponse(ResponseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(RequestModel):
    refresh_token: str
