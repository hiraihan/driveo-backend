import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine

async def test_register_and_login(client):
    ac = client
    response = await ac.post("/auth/register", json={"email": "test@example.com", "password": "password123", "role_name": "Penyewa"})
    assert response.status_code == 201
    
    response = await ac.post("/auth/login", data={"username": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

async def test_rbac_dependency(client):
    from app.modules.auth.dependencies import depends_on_role
    assert callable(depends_on_role)
