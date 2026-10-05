import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import Base, engine
import jwt
from datetime import datetime, timedelta

def create_mock_token(user_id: str, role: str):
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(to_encode, "test_secret_key", algorithm="HS256")

async def test_rental_verification(client):
    from app.modules.rental.models import Rental
    from app.core.database import async_session
    
    rental_id = "test-rental-id"
    async with async_session() as session:
        rental = Rental(id=rental_id, nama_usaha="Rental Test", status_verifikasi="MENUNGGU")
        session.add(rental)
        await session.commit()

    token = create_mock_token("admin-user-id", "Admin")
    
    ac = client
    response = await ac.post(f"/rentals/{rental_id}/verify", headers={"Authorization": f"Bearer {token}"}, json={
        "status": "LOLOS",
        "alasan": "Semua dokumen valid"
    })
    assert response.status_code == 200
    
    # Verify status changed
    async with async_session() as session2:
        from sqlalchemy.future import select
        result = await session2.execute(select(Rental).where(Rental.id == rental_id))
        r = result.scalars().first()
        assert r.status_verifikasi == "LOLOS"
