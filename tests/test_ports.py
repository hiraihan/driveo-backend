import json
from sqlalchemy import select
from app.contracts.ports import AuditPort, NotificationPort
from app.modules.audit.service import AuditService
from app.modules.notification.service import NotificationService
from app.modules.audit.models import AuditLog
from app.modules.notification.models import Notification

async def test_audit_service_is_port_and_persists(db):
    svc = AuditService(db)
    assert isinstance(svc, AuditPort)
    await svc.log_event("RENTAL_VERIFIED", {"rental_id": "r1"}, actor_id="admin1")
    await db.commit()
    row = (await db.execute(select(AuditLog))).scalar_one()
    assert (row.event_name, row.actor_id, json.loads(row.payload)) == ("RENTAL_VERIFIED", "admin1", {"rental_id": "r1"})

async def test_notification_service_is_port_and_persists(db):
    svc = NotificationService(db)
    assert isinstance(svc, NotificationPort)
    await svc.send("u@x.com", "Halo", subject="Tes")
    await db.commit()
    assert (await db.execute(select(Notification))).scalar_one().status == "SENT"
