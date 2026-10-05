from tests.factories import make_user, auth_header
from app.core.enums import UserRole
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
import jwt
from datetime import datetime, timedelta

async def test_rental_onboarding(client, db):
    u = await make_user(db)
    
    response = await client.post("/rentals/onboard", headers=auth_header(u), json={
        "nama_usaha": "Rental Jaya",
        "nib": "123456789",
        "alamat": "Jl. Test No. 1",
        "kontak": "08123456789",
        "payout_account": "1234567890"
    })
    assert response.status_code == 201
