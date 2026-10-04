import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
import jwt
from datetime import datetime, timedelta

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def create_mock_token(user_id: str, role: str):
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(to_encode, "test_secret_key", algorithm="HS256")

@pytest.mark.asyncio(loop_scope="function")
async def test_get_and_update_user_profile():
    from app.modules.user.models import User
    from app.core.database import async_session
    
    # Create test user
    user_id = "test-user-id"
    async with async_session() as session:
        user = User(id=user_id, email="me@example.com", password_hash="hash", role_id="role1")
        session.add(user)
        await session.commit()

    token = create_mock_token(user_id, "Penyewa")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"
        
        # Give consent (BR-040)
        consent_response = await ac.post("/users/me/consents", headers={"Authorization": f"Bearer {token}"}, json={"document_type": "KTP", "version": "1.0"})
        assert consent_response.status_code == 201
