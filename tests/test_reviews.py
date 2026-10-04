import pytest
import pytest_asyncio
from app.core.database import Base, engine
from sqlalchemy.future import select
import uuid
from app.modules.review.models import Review

@pytest_asyncio.fixture(autouse=True)
async def prepare_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio(loop_scope="function")
async def test_review_model():
    from app.core.database import async_session
    
    async with async_session() as session:
        r = Review(booking_id="b1", user_id="u1", rental_id="r1", rating=5, komentar="Bagus")
        session.add(r)
        await session.commit()
        
        result = await session.execute(select(Review).where(Review.rating == 5))
        review = result.scalars().first()
        assert review.komentar == "Bagus"
