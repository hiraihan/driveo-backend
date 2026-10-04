import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio(loop_scope="function")
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={"email": "test@example.com", "password": "password123", "role_name": "Penyewa"})
        assert response.status_code == 201
        
        response = await ac.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token is not None

@pytest.mark.asyncio(loop_scope="function")
async def test_rbac_dependency():
    from app.modules.auth.dependencies import depends_on_role
    assert callable(depends_on_role)
