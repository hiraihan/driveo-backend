from seed import seed_data
from sqlalchemy import select
from app.modules.user.models import User

async def test_seed_idempotent(db, monkeypatch):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "seed_admin_password", "admin-pass-123")
    await seed_data(db)
    await seed_data(db)
    result = await db.execute(select(User).where(User.email == "admin@driveo.com"))
    assert len(result.scalars().all()) == 1
