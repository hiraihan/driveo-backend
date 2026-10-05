from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.core.errors import register_error_handlers, NotFound, InvalidTransition
from app.core.pagination import Page, PageMeta
from app.core.time import today_wib

def _app():
    a = FastAPI(); register_error_handlers(a)
    @a.get("/nf")
    async def nf(): raise NotFound()
    @a.get("/it")
    async def it(): raise InvalidTransition("SELESAI", "CANCEL")
    @a.get("/v")
    async def v(n: int): return n
    return a

async def _get(path):
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://t") as c:
        return await c.get(path)

async def test_not_found_envelope():
    r = await _get("/nf")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"

async def test_invalid_transition_envelope():
    r = await _get("/it")
    assert r.status_code == 409
    assert r.json()["error"] == {"code": "INVALID_STATE_TRANSITION", "message": r.json()["error"]["message"],
                                 "details": {"state": "SELESAI", "event": "CANCEL"}}

async def test_validation_envelope():
    r = await _get("/v?n=abc")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"

async def test_health(client):
    r = await client.get("/health")
    assert r.json() == {"status": "ok"}

async def test_cors_preflight(client):
    r = await client.options("/health", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_page_meta_total_pages():
    assert PageMeta(page=2, page_size=20, total_items=45, total_pages=3).total_pages == 3

def test_today_wib_is_utc_plus_7(monkeypatch):
    import app.core.time as t, datetime as dt
    monkeypatch.setattr(t, "utcnow", lambda: dt.datetime(2026, 1, 1, 18, 0, tzinfo=dt.timezone.utc))
    assert t.today_wib() == dt.date(2026, 1, 2)
