import pytest
from tests.factories import make_user, make_admin, auth_header
from app.core.enums import UserRole
from app.modules.notification.models import Notification
from app.core.ids import new_id

@pytest.mark.asyncio
async def test_get_my_notifications(client, db):
    user = await make_user(db)
    
    n1 = Notification(id=new_id(), recipient=user.email, type="EMAIL", body="Hello")
    n2 = Notification(id=new_id(), recipient="someone@example.com", type="EMAIL", body="Other")
    db.add_all([n1, n2])
    await db.commit()
    
    headers = auth_header(user, UserRole.PENYEWA)
    res = await client.get("/notifications/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    assert len(data) == 1
    assert data[0]["body"] == "Hello"

@pytest.mark.asyncio
async def test_get_all_notifications_admin(client, db):
    admin = await make_admin(db)
    
    n1 = Notification(id=new_id(), recipient="a@example.com", type="EMAIL", body="Hello A")
    n2 = Notification(id=new_id(), recipient="b@example.com", type="EMAIL", body="Hello B")
    db.add_all([n1, n2])
    await db.commit()
    
    headers = auth_header(admin, UserRole.ADMIN)
    res = await client.get("/notifications", headers=headers)
    assert res.status_code == 200
    data = res.json()
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    # At least 2 because of previous tests might pollute, but memory db is fresh? 
    # Let's just check it returns a list and has status 200.
    assert len(data) >= 2
