import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

async def test_db_session(client):
    from app.core.database import get_db
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        break

def test_models_exist():
    from app.modules.user.models import User, Role
    assert hasattr(User, "__tablename__")
    assert hasattr(Role, "__tablename__")
