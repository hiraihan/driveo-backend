import os
os.environ["DRIVEO_JWT_SECRET"] = "t" * 40

import pytest
from httpx import AsyncClient, ASGITransport
from app.core.database import engine, async_session
from app.main import app
from app.models import Base

@pytest.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db():
    async with async_session() as session:
        yield session

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test/api/v1"
    ) as ac:
        yield ac
