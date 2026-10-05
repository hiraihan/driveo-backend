from tests.factories import make_user, auth_header
from app.core.enums import UserRole
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
import jwt
from datetime import datetime, timedelta

async def test_get_and_update_user_profile(client, db):
    u = await make_user(db)
    
    response = await client.get("/users/me", headers=auth_header(u))
    assert response.status_code == 200
