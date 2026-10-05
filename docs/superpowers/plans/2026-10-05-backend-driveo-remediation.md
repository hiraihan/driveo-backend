# DriveO Backend Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every finding in the review (C1–C7, H1–H11, API/architecture/data/test sections) so the full rental flow — register → eKYC → search → booking → DP → confirm → pelunasan → handover → return → review, plus cancel/refund/expiry — works end-to-end, securely, behind a consistent API.

**Architecture:** Keep the FastAPI modular monolith. Each module gets `schemas.py` (Pydantic I/O), `service.py` (business logic, the only thing other modules may import) and a thin `routers.py`. Shared concerns live in `app/core/` (config, errors, pagination, enums, time, ids). Booking lifecycle is driven by one explicit transition table; money moves only through an append-only escrow ledger.

**Tech Stack:** Python 3.14, FastAPI 0.142, SQLAlchemy 2.1 async, Pydantic v2 + pydantic-settings, PyJWT, passlib[bcrypt], aiosqlite (dev/test), asyncpg + Alembic (prod), pytest + pytest-asyncio + httpx.

**Spec:** `docs/superpowers/specs/2026-10-05-backend-driveo-review.md` (review report). Original intent: `docs/superpowers/plans/2026-10-04-backend-driveo-dev-a.md`, `...-dev-b.md`.

**Phases:** Phase 0 (Tasks 1–5) = foundations + security hotfix. Phase 1 (Tasks 6–19) = flow continuity. Phase 2 (Tasks 20–21) = persistence + E2E. Each phase leaves the suite green and the app runnable.

## Global Constraints

- All routes mounted under `/api/v1`. OAuth2 `tokenUrl="/api/v1/auth/login"`.
- Every error response: `{"error": {"code": "<UPPER_SNAKE>", "message": "<Bahasa Indonesia>", "details": <any|null>}}`. No raw `{"detail": ...}`.
- Every request schema subclasses `app.core.schemas.RequestModel` (`extra="forbid"`); every endpoint declares `response_model` (subclass of `ResponseModel`, `from_attributes=True`).
- Naming: snake_case fields; domain nouns stay Indonesian as already used (`tanggal_mulai`, `nama_usaha`, `komentar`); meta fields English (`id`, `status`, `created_at`); enum values UPPER_SNAKE; error codes English UPPER_SNAKE; messages Indonesian.
- Status codes: create → 201, async accept (webhook) → 200, not found → 404, not owner/role → 403, unauthenticated → 401, duplicate/illegal state/slot taken → 409, validation → 422.
- Money: `int` rupiah everywhere (`BigInteger` column). No `float` for money.
- IDs: `app.core.ids.new_id()` → `str(uuid.uuid7())` (NFR-DB-001), `String(36)` columns.
- Time: store UTC tz-aware (`DateTime(timezone=True)`, `app.core.time.utcnow()`); business dates (H-x, "today") use `app.core.time.today_wib()` (UTC+7). Never `datetime.utcnow()`.
- Business numbers come from `Settings`, never literals: `dp_percent=30` (OQ-001), `dp_expiry_minutes=60` (OQ-002), `rental_confirm_sla_minutes=120` (OQ-003), `listing_stale_days=7`, `default_max_vehicles=5`, `max_upload_bytes=5_000_000`.
- Module boundary: code in `app/modules/X` may import `app/modules/Y/service.py` or `Y/schemas.py`, never `Y/models.py` (enforced by test in Task 21).
- Audit (`AuditService.log_event`) on: rental verify, verification review, booking create/cancel/confirm/reject/expire/handover/complete, payment received, refund, escrow release, promo/membership create.
- Services never `commit()`; routers/jobs own the transaction.
- Run tests with: `source venv/bin/activate && pytest <path> -v` (pytest.ini sets `pythonpath=.`, `asyncio_mode=auto`).

## Review Focus

1. Late DP webhook arriving after the booking auto-expired → booking stays `DIBATALKAN`, the DP is fully refunded, slots are not re-locked (test in Task 14).
2. Overlapping booking that shares only one boundary day with an existing booking → 409 `SLOT_UNAVAILABLE`; adjacent (non-overlapping) range → 201 (test in Task 13).
3. Same Midtrans notification delivered twice → one `Payment` success, one ledger `HOLD`, both deliveries 200 (test in Task 14).
4. Single-day booking (`tanggal_mulai == tanggal_selesai`) and totals not divisible by DP% → charged for exactly 1 day and `dp + sisa == total_nilai` (test in Task 13).
5. Penyewa cancels on H-0 after paying DP → refund 0, slots released, escrow balance 0 with a `RELEASE` entry equal to the DP (test in Task 15).

---

## File Structure

```
app/
  main.py                      # create_app(): lifespan, CORS, error handlers, routers under /api/v1
  jobs.py                      # periodic DP-expiry + SLA jobs (Task 16)
  models.py                    # imports every module's models (alembic + create_all) (Task 20)
  core/
    config.py  errors.py  pagination.py  enums.py  time.py  ids.py  schemas.py  database.py
  contracts/ports.py           # async Protocols (Task 4)
  mocks/ports.py               # async mocks matching Protocols (Task 4)
  modules/<module>/{models,schemas,service,routers}.py
tests/
  conftest.py  factories.py  test_<module>.py  test_e2e_flow.py  test_boundaries.py
pytest.ini  requirements.txt  README.md
```

Module ownership after the plan: `auth` (tokens, deps), `user` (profile, consent, role assignment), `rental` (onboard, verify, staff, dashboard), `vehicle`, `availability` (slots), `listing`, `search`, `verification` (eKYC), `booking` (state, pricing, lifecycle, checklists), `payment` (intents, webhook, escrow ledger), `refund`, `review`, `admin` (membership, promo), `notification`, `audit`.

---

## Phase 0 — Foundations & Security Hotfix

### Task 1: Config, dependencies, shared test infrastructure

**Files:**
- Create: `app/core/config.py`, `pytest.ini`, `requirements.txt`, `tests/conftest.py`, `tests/factories.py`, `tests/test_config.py`
- Modify: `.gitignore` (remove the `docs/` line), every `tests/test_*.py` (delete local `prepare_db` fixtures and `@pytest.mark.asyncio(...)` decorators)

**Interfaces:**
- Produces: `Settings` (env prefix `DRIVEO_`), `get_settings() -> Settings` (`lru_cache`). Fields: `env: Literal["dev","demo","prod"]="dev"`, `jwt_secret: str = Field(min_length=32)` (required), `jwt_algorithm="HS256"`, `access_token_minutes=30`, `refresh_token_days=7`, `database_url="sqlite+aiosqlite:///:memory:"`, `cors_origins: list[str]=["http://localhost:3000"]`, `dp_percent: float=30.0`, `dp_expiry_minutes=60`, `rental_confirm_sla_minutes=120`, `listing_stale_days=7`, `default_max_vehicles=5`, `upload_dir="uploads"`, `max_upload_bytes=5_000_000`, `midtrans_server_key="dev-server-key"`, `job_interval_seconds=60`, `seed_on_startup=False`, `seed_admin_password: str|None=None`.
- Produces (tests): fixtures `db` (AsyncSession), `client` (httpx `AsyncClient`, `base_url="http://test/api/v1"`), autouse `prepare_db`; `tests/factories.py` module (factories added by later tasks).

- [ ] **Step 1: Write failing tests** in `tests/test_config.py`

```python
import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_missing_secret_rejected(monkeypatch):
    monkeypatch.delenv("DRIVEO_JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

def test_short_secret_rejected():
    with pytest.raises(ValidationError):
        Settings(jwt_secret="short")

def test_business_defaults():
    s = Settings(jwt_secret="x" * 32)
    assert (s.dp_percent, s.dp_expiry_minutes, s.rental_confirm_sla_minutes) == (30.0, 60, 120)
```

- [ ] **Step 2: Run** `pytest tests/test_config.py -v` → FAIL (`ModuleNotFoundError: app.core.config`).
- [ ] **Step 3: Implement** `app/core/config.py`; `pytest.ini` with `pythonpath = .`, `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`, `testpaths = tests`; `requirements.txt` pinning the versions currently in `venv` (`pip freeze` for fastapi, sqlalchemy, pydantic, pydantic-settings, PyJWT, passlib, bcrypt, aiosqlite, asyncpg, alembic, python-multipart, uvicorn, httpx, pytest, pytest-asyncio) plus `email-validator`; then `pip install email-validator`. `tests/conftest.py` sets `os.environ["DRIVEO_JWT_SECRET"] = "t" * 40` **before** any `app` import, and moves the shared `prepare_db` (create_all/drop_all) there.
- [ ] **Step 4: Run** `pytest -v` → all existing 31 tests + 3 new PASS.
- [ ] **Step 5: Commit**

```bash
git add .gitignore pytest.ini requirements.txt app/core/config.py tests/ docs/
git commit -m "chore: add settings, requirements, shared test fixtures; track docs"
```

---

### Task 2: App bootstrap, error envelope, core helpers

**Files:**
- Create: `app/core/errors.py`, `app/core/pagination.py`, `app/core/enums.py`, `app/core/time.py`, `app/core/ids.py`, `app/core/schemas.py`, `tests/test_core.py`
- Modify: `app/main.py` (rewrite), `app/core/database.py` (engine from `get_settings().database_url`), `app/modules/auth/dependencies.py:5` (tokenUrl), all existing tests' URLs (now relative to `/api/v1` via `client`)

**Interfaces:**
- Produces `app/core/errors.py`: `AppError(code: str, message: str, status_code: int = 400, details: Any = None)`; `NotFound(message="Data tidak ditemukan")` (404, `NOT_FOUND`); `Forbidden(message="Akses ditolak")` (403, `FORBIDDEN`); `Unauthorized(code="UNAUTHORIZED", message=...)` (401); `Conflict(code: str, message: str)` (409); `InvalidTransition(state: str, event: str)` (409, `INVALID_STATE_TRANSITION`, details `{"state","event"}`); `ValidationFailed(code: str, message: str)` (422); `register_error_handlers(app: FastAPI) -> None` handling `AppError`, `RequestValidationError` (422 `VALIDATION_ERROR`, details=`exc.errors()`), `StarletteHTTPException` (code from status: 401 `UNAUTHORIZED`, 403 `FORBIDDEN`, 404 `NOT_FOUND`, 405 `METHOD_NOT_ALLOWED`, else `HTTP_ERROR`), `IntegrityError` (409 `CONFLICT`).
- Produces `app/core/pagination.py`: `PageParams` dependency (`page: int = Query(1, ge=1)`, `page_size: int = Query(20, ge=1, le=100)`); `PageMeta(page, page_size, total_items, total_pages)`; `Page[T](data: list[T], pagination: PageMeta)`; `async def paginate(db, stmt, params: PageParams, item_schema: type[T]) -> Page[T]`.
- Produces `app/core/enums.py` (`StrEnum`s): `UserRole{ADMIN="Admin", RENTAL="Rental", PENYEWA="Penyewa"}`; `BookingState{MENUNGGU_DP, MENUNGGU_KONFIRMASI_RENTAL, TERKONFIRMASI, BERJALAN, SELESAI, DIBATALKAN, DITOLAK}`; `BookingEvent{DP_PAID, CONFIRM, REJECT, CANCEL, EXPIRE, SLA_BREACH, HANDOVER, RETURN}`; `EscrowState{NONE, DITAHAN_ESCROW, LUNAS, DICAIRKAN, DIKEMBALIKAN}`; `LedgerEntryType{HOLD, RELEASE, REFUND}`; `SlotStatus{DIPESAN, DIBLOKIR}`; `RentalStatus{MENUNGGU, LOLOS, DITOLAK}`; `VerificationStatus{MENUNGGU, TERVERIFIKASI, DITOLAK}`; `PaymentType{DP, PELUNASAN}`; `PaymentStatus{PENDING, BERHASIL, GAGAL}`; `ListingStatus{DRAFT, PUBLISHED, ARCHIVED}`; `VehicleStatus{AKTIF, NONAKTIF}`; `ChecklistType{HANDOVER, RETURN}`. Values equal names except `UserRole`.
- Produces: `utcnow() -> datetime` (tz-aware UTC), `today_wib() -> date`; `new_id() -> str`; `RequestModel`, `ResponseModel`.
- Produces `app/main.py`: `create_app() -> FastAPI`; module-level `app = create_app()`; `lifespan` runs `create_all` (and, from Task 16, the job loop; seed only if `settings.seed_on_startup`); `CORSMiddleware` with `settings.cors_origins`; `GET /api/v1/health -> {"status": "ok"}`; all routers included on an `APIRouter(prefix="/api/v1")`. Replaces `@app.on_event`.

- [ ] **Step 1: Write failing tests** in `tests/test_core.py`

```python
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
    monkeypatch.setattr(t, "utcnow", lambda: dt.datetime(2026, 1, 1, 18, 0, tzinfo=dt.UTC))
    assert t.today_wib() == dt.date(2026, 1, 2)
```

- [ ] **Step 2: Run** `pytest tests/test_core.py -v` → FAIL (imports missing).
- [ ] **Step 3: Implement** the core modules and `create_app()`. `paginate` runs `select(func.count()).select_from(stmt.subquery())` then `stmt.limit().offset()`; `total_pages = ceil(total/page_size)` (0 when empty). Update existing HTTP tests to use the `client` fixture.
- [ ] **Step 4: Run** `pytest -v` → all PASS.
- [ ] **Step 5: Commit** `git commit -am "feat(core): error envelope, pagination, enums, /api/v1, lifespan, CORS, health"` (add new files first).

---

### Task 3: Auth hardening (C2, C3) and safe seeding

**Files:**
- Create: `app/modules/auth/security.py`, `app/modules/auth/schemas.py`, `app/modules/user/service.py`
- Modify: `app/modules/auth/routers.py`, `app/modules/auth/dependencies.py`, `app/modules/user/models.py` (ids via `new_id`, `created_at`), `seed.py`, every router using `current_user["sub"]` → `current_user.id`, `depends_on_role` → `require_roles`
- Test: `tests/test_auth.py` (replace), `tests/test_seed.py`; add `make_user`, `auth_header` to `tests/factories.py`

**Interfaces:**
- Produces `security.py`: `hash_password(p: str) -> str`, `verify_password(p: str, h: str) -> bool`, `create_access_token(user_id: str, role: UserRole) -> str` (claims `sub`, `role`, `type="access"`, `exp`), `create_refresh_token(user_id: str) -> str` (`type="refresh"`), `decode_token(token: str, expected_type: Literal["access","refresh"]) -> dict` (raises `Unauthorized("INVALID_TOKEN", ...)`). Secret/algorithm only from `get_settings()`; delete both `SECRET_KEY` constants.
- Produces `dependencies.py`: `CurrentUser(BaseModel): id: str; email: str; role: UserRole`; `async def get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)) -> CurrentUser` (loads user; missing or `is_active=False` → 401 `INVALID_TOKEN`; role read from DB, not the token); `require_roles(*roles: UserRole)` → dependency returning `CurrentUser`, else 403.
- Produces `user/service.py`: `get_or_create_role(db, role: UserRole) -> Role`, `get_user(db, user_id) -> User | None`, `get_user_role(db, user: User) -> UserRole`, `set_user_role(db, user_id: str, role: UserRole) -> None`.
- Produces endpoints: `POST /auth/register` body `RegisterRequest(email: EmailStr, password: str = Field(min_length=8))` → 201 `UserResponse(id, email, role)`; always `UserRole.PENYEWA`; duplicate → 409 `EMAIL_TAKEN`. `POST /auth/login` (OAuth2 form) → `TokenResponse(access_token, refresh_token, token_type="bearer")`; bad creds → 401 `INVALID_CREDENTIALS`. `POST /auth/refresh` body `RefreshRequest(refresh_token)` → `TokenResponse`. `GET /users/me` returns `UserResponse` with role **name**.
- Produces (tests): `async def make_user(db, role=UserRole.PENYEWA, email=None, is_active=True) -> User`; `def auth_header(user: User, role: UserRole | None = None) -> dict`.
- `seed.py`: `async def seed_data(session) -> None` idempotent (returns early if `admin@driveo.com` exists); admin password from `settings.seed_admin_password` (skip admin if `None`); demo data only when `settings.env != "prod"`.

- [ ] **Step 1: Write failing tests** (`tests/test_auth.py`)

```python
import jwt
from tests.factories import make_user, auth_header
from app.core.enums import UserRole

async def test_register_always_penyewa(client):
    r = await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    assert r.status_code == 201 and r.json()["role"] == "Penyewa"

async def test_register_rejects_role_field(client):
    r = await client.post("/auth/register", json={"email": "a@x.com", "password": "password1", "role_name": "Admin"})
    assert r.status_code == 422

async def test_register_duplicate_email(client):
    body = {"email": "a@x.com", "password": "password1"}
    await client.post("/auth/register", json=body)
    r = await client.post("/auth/register", json=body)
    assert r.status_code == 409 and r.json()["error"]["code"] == "EMAIL_TAKEN"

async def test_register_short_password(client):
    assert (await client.post("/auth/register", json={"email": "a@x.com", "password": "123"})).status_code == 422

async def test_login_and_refresh(client):
    await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    tok = (await client.post("/auth/login", data={"username": "a@x.com", "password": "password1"})).json()
    r = await client.post("/auth/refresh", json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 200 and r.json()["access_token"]
    r = await client.post("/auth/refresh", json={"refresh_token": tok["access_token"]})
    assert r.status_code == 401

async def test_login_wrong_password(client):
    await client.post("/auth/register", json={"email": "a@x.com", "password": "password1"})
    r = await client.post("/auth/login", data={"username": "a@x.com", "password": "nope-nope"})
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"

async def test_forged_token_rejected(client, db):
    u = await make_user(db)
    forged = jwt.encode({"sub": u.id, "role": "Admin", "type": "access"}, "test_secret_key", algorithm="HS256")
    assert (await client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})).status_code == 401

async def test_inactive_user_rejected(client, db):
    u = await make_user(db, is_active=False)
    assert (await client.get("/users/me", headers=auth_header(u))).status_code == 401

async def test_role_comes_from_db_not_token(client, db):
    u = await make_user(db)  # Penyewa
    r = await client.post("/admin/promos", headers=auth_header(u, role=UserRole.ADMIN),
                          json={"code": "X", "discount_percent": 10, "max_discount_amount": 1, "valid_until": "2030-01-01"})
    assert r.status_code == 403

async def test_me_returns_role_name(client, db):
    u = await make_user(db)
    assert (await client.get("/users/me", headers=auth_header(u))).json()["role"] == "Penyewa"
```

`tests/test_seed.py`: run `seed_data` twice with `seed_admin_password="admin-pass-123"` → exactly one user with email `admin@driveo.com`.

- [ ] **Step 2: Run** `pytest tests/test_auth.py tests/test_seed.py -v` → FAIL.
- [ ] **Step 3: Implement** per Interfaces. Update `tests/test_user.py`, `test_rental.py`, `test_rental_verification.py` to use `make_user` + `auth_header` (fake user ids no longer authenticate).
- [ ] **Step 4: Run** `pytest -v` → all PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(auth): block role self-assignment, env JWT secret, refresh tokens, DB-backed roles, idempotent seed"`

---

### Task 4: Async ports + real Audit and Notification adapters

**Files:**
- Modify: `app/contracts/ports.py`, `app/mocks/ports.py`, `app/modules/audit/models.py`, `app/modules/notification/models.py`, `app/modules/notification/service.py`
- Create: `app/modules/audit/service.py`
- Test: `tests/test_ports.py` (replaces `test_contracts.py`, `test_mocks.py`, `test_b_mocks.py`, `test_notification.py`, `test_verification_audit.py`)

**Interfaces:**
- Produces `ports.py` (all `@runtime_checkable Protocol`, all methods `async`): `AuditPort.log_event(event_name: str, payload: dict, actor_id: str | None = None) -> None`; `NotificationPort.send(recipient: str, message: str, subject: str | None = None, channel: str = "EMAIL") -> None`; `VerificationReadPort.get_status(user_id: str) -> VerificationStatus`; `RentalReadPort.get_rental_status(rental_id: str) -> RentalStatus`; `RefundPort.trigger_refund(booking_id: str, amount: int, reason: str) -> str`; `EscrowReadPort.get_state(booking_id: str) -> EscrowState`. Drop `BookingPort` and `PaymentReadPort` (replaced by `booking.service` / `payment.service` calls per the boundary rule).
- Produces: `AuditService(db)` implementing `AuditPort` (stores `payload` as JSON text, `actor_id` column, `timestamp` UTC; no update/delete methods); `NotificationService(db)` implementing `NotificationPort` (inserts `Notification(status="SENT")`, no commit). Remove `send_email`.
- Mocks in `app/mocks/ports.py` become async and are used only by tests.

- [ ] **Step 1: Write failing tests**

```python
from app.contracts.ports import AuditPort, NotificationPort
from app.modules.audit.service import AuditService
from app.modules.notification.service import NotificationService
from app.modules.audit.models import AuditLog
from app.modules.notification.models import Notification
from sqlalchemy import select
import json

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
```

- [ ] **Step 2: Run** `pytest tests/test_ports.py -v` → FAIL.
- [ ] **Step 3: Implement**; delete the replaced test files.
- [ ] **Step 4: Run** `pytest -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "refactor(ports): async protocols, real audit and notification adapters"`

---

### Task 5: Admin and notification endpoint hardening (C7, stubs)

**Files:**
- Modify: `app/modules/admin/routers.py`, `app/modules/admin/models.py` (money `BigInteger`, ids), `app/modules/notification/routers.py`, `app/main.py` (drop availability router), delete `app/modules/availability/routers.py` (rebuilt in Task 8)
- Create: `app/modules/admin/schemas.py`, `app/modules/notification/schemas.py`
- Test: `tests/test_admin.py` (replaces `test_admin_promo.py`), `tests/test_notification_api.py`; add `make_admin` to factories

**Interfaces:**
- `PromoCreate(code: str = Field(pattern=r"^[A-Z0-9]{3,20}$"), discount_percent: float = Field(gt=0, le=100), max_discount_amount: int = Field(gt=0), valid_until: date)`; `PromoResponse` adds `id, is_active`. `MembershipCreate(name, price: int = Field(ge=0), max_vehicles: int = Field(ge=1), max_staff: int = Field(ge=1))`.
- `POST /admin/promos`, `POST /admin/memberships` → Admin, 201, audit `PROMO_CREATED`/`MEMBERSHIP_CREATED`, duplicate → 409 `PROMO_CODE_TAKEN` / `MEMBERSHIP_NAME_TAKEN`.
- `GET /admin/promos` → Admin only, `Page[PromoResponse]`. `GET /admin/memberships` → public, `list[MembershipResponse]` (pricing page).
- `GET /notifications/me` → auth, `Page[NotificationResponse]` filtered by `current_user.email`. `GET /notifications?recipient=` → Admin only. Remove `/notifications/inbox/{recipient}`.
- Produces (admin service, for Task 13): `app/modules/admin/service.py`: `async def get_valid_promo(db, code: str, today: date) -> Promo` raising `ValidationFailed("PROMO_INVALID", "Kode promo tidak valid atau kedaluwarsa")`.

- [ ] **Step 1: Write failing tests**

```python
async def test_promo_list_requires_admin(client, db):
    assert (await client.get("/admin/promos")).status_code == 401
    u = await make_user(db)
    assert (await client.get("/admin/promos", headers=auth_header(u))).status_code == 403

async def test_promo_duplicate_and_bounds(client, db):
    h = auth_header(await make_admin(db))
    body = {"code": "HEMAT10", "discount_percent": 10, "max_discount_amount": 50000, "valid_until": "2030-01-01"}
    assert (await client.post("/admin/promos", json=body, headers=h)).status_code == 201
    assert (await client.post("/admin/promos", json=body, headers=h)).json()["error"]["code"] == "PROMO_CODE_TAKEN"
    assert (await client.post("/admin/promos", json={**body, "code": "X2X", "discount_percent": 150}, headers=h)).status_code == 422

async def test_memberships_public(client):
    assert (await client.get("/admin/memberships")).status_code == 200

async def test_get_valid_promo_expired(db):  # admin.service
    ...  # create promo valid_until=yesterday → pytest.raises(ValidationFailed) with code PROMO_INVALID

async def test_inbox_only_own(client, db):
    a, b = await make_user(db, email="a@x.com"), await make_user(db, email="b@x.com")
    await NotificationService(db).send("b@x.com", "rahasia"); await db.commit()
    r = await client.get("/notifications/me", headers=auth_header(a))
    assert r.json()["pagination"]["total_items"] == 0
    assert (await client.get("/notifications/inbox/b@x.com")).status_code == 404

async def test_availability_stub_removed(client):
    assert (await client.post("/availability")).status_code == 404
```

- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** `pytest -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(admin,notification): lock down promo list and inbox, validate inputs, remove availability stub"`

---

## Phase 1 — Flow Continuity

### Task 6: Rental onboarding, ownership, verification (H10)

**Files:**
- Modify: `app/modules/rental/models.py` (ids, `RentalStaff` unique `user_id`), `app/modules/rental/routers.py`
- Create: `app/modules/rental/schemas.py`, `app/modules/rental/service.py`
- Test: `tests/test_rental.py` (replace both rental test files); factories `make_rental(db, owner: User, status=RentalStatus.LOLOS) -> Rental`

**Interfaces:**
- Consumes: `set_user_role` (Task 3), `AuditService` (Task 4).
- Produces `rental/service.py`: `get_rental(db, rental_id) -> Rental` (NotFound); `get_rental_id_for_staff(db, user_id) -> str | None`; `assert_rental_staff(db, user_id: str, rental_id: str) -> None` (Forbidden); `vehicle_limit(db, rental_id) -> int` (membership `max_vehicles` or `settings.default_max_vehicles`); `RentalReadService(db)` implementing `RentalReadPort`; `rental_ids_matching_location(db, lokasi: str) -> set[str]` (LOLOS rentals whose `alamat` ilike `%lokasi%`, used by Task 10).
- Endpoints: `POST /rentals/onboard` (`OnboardRequest(nama_usaha, nib, alamat, kontak, payout_account)`) → 201 `RentalResponse(id, nama_usaha, nib, alamat, kontak, status_verifikasi)`; user already staff → 409 `ALREADY_RENTAL_STAFF`; sets user role to `Rental`. `GET /rentals/me` → staff only. `GET /rentals/{id}` → public `RentalResponse`. `POST /rentals/{id}/verify` (Admin; `VerifyRequest(status: Literal[RentalStatus.LOLOS, RentalStatus.DITOLAK], alasan: str | None)`) → `RentalResponse`, audit `RENTAL_VERIFIED`, notification to owner email. Payout account stays mock-encrypted (`ENCRYPTED_` prefix) and is never returned.

- [ ] **Step 1: Write failing tests**: `test_onboard_promotes_to_rental` (after onboard, `GET /users/me` role == "Rental", status_verifikasi == "MENUNGGU"); `test_onboard_twice_409`; `test_verify_rejects_unknown_status` (`"TERSERAH"` → 422); `test_verify_requires_admin` (Rental user → 403); `test_verify_writes_audit` (AuditLog `RENTAL_VERIFIED` with `actor_id` == admin id); `test_payout_not_exposed` (`"payout_account" not in` any response body).
- [ ] **Step 2: Run** `pytest tests/test_rental.py -v` → FAIL. **Step 3: Implement.** **Step 4:** `pytest -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(rental): onboarding promotes role, ownership helpers, validated verification with audit"`

---

### Task 7: Vehicle CRUD with ownership and quota (H8)

**Files:**
- Modify: `app/modules/vehicle/models.py` (`tarif_dasar` BigInteger, `plat_nomor` unique, `status` VehicleStatus, `updated_at`), `app/modules/vehicle/routers.py`
- Create: `app/modules/vehicle/schemas.py`, `app/modules/vehicle/service.py`
- Test: `tests/test_vehicle.py` (replace); factory `make_vehicle(db, rental: Rental, **kw) -> Vehicle`

**Interfaces:**
- Consumes: `get_rental_id_for_staff`, `assert_rental_staff`, `vehicle_limit` (Task 6).
- Produces `vehicle/service.py`: `get_vehicle(db, vehicle_id) -> Vehicle` (NotFound if missing or `is_deleted`); `assert_vehicle_owner(db, user_id, vehicle_id) -> Vehicle`.
- Endpoints: `POST /vehicles` (Rental; body `VehicleCreate(jenis, merk, tipe, plat_nomor, tarif_dasar: int = Field(gt=0))` — **no `rental_id`**, taken from staff) → 201; quota reached → 409 `VEHICLE_LIMIT_REACHED`; duplicate plate → 409 `PLATE_TAKEN`. `GET /vehicles?rental_id=` → `Page[VehicleResponse]`. `GET /vehicles/{id}`. `PATCH /vehicles/{id}` (`VehicleUpdate` all optional incl. `status`). `DELETE /vehicles/{id}` → 204 soft delete.

- [ ] **Step 1: Failing tests**: `test_create_uses_staff_rental` (response `rental_id` == own rental even though another rental exists); `test_body_rental_id_rejected` (422); `test_non_positive_tarif` (422); `test_quota` (6th vehicle with default limit 5 → 409 `VEHICLE_LIMIT_REACHED`); `test_patch_other_rental_403`; `test_soft_delete_hides` (DELETE → 204, then GET → 404, list excludes it).
- [ ] **Step 2–4:** run → FAIL, implement, `pytest -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(vehicle): ownership-scoped CRUD, membership quota, soft delete"`

---

### Task 8: Availability calendar with DB-enforced slot lock (H3, C6 groundwork)

**Files:**
- Modify: `app/modules/vehicle/models.py` → move `VehicleAvailability` to `app/modules/availability/models.py` (fields: `id, vehicle_id, tanggal, status: SlotStatus, booking_id: str | None`, `UniqueConstraint("vehicle_id", "tanggal")`)
- Create: `app/modules/availability/{models,schemas,service,routers}.py`
- Modify: `app/main.py` (mount availability router)
- Test: `tests/test_availability.py`

**Interfaces:**
- Consumes: `assert_vehicle_owner` (Task 7).
- Produces `availability/service.py`: `lock_slots(db, vehicle_id: str, start: date, end: date, booking_id: str) -> None` — inserts one `DIPESAN` row per day inside `db.begin_nested()`; `IntegrityError` → `Conflict("SLOT_UNAVAILABLE", "Kendaraan tidak tersedia pada tanggal tersebut")`. `release_slots(db, booking_id: str) -> int` (deletes only that booking's rows). `block_dates(db, vehicle_id, dates: list[date]) -> None` (`DIBLOKIR`, same conflict handling). `unblock_date(db, vehicle_id, tanggal) -> None` (only `DIBLOKIR` rows; booked → 409 `SLOT_BOOKED`). `blocked_vehicle_ids(db, start: date, end: date) -> set[str]`. Free days have **no row** (the old `"tersedia"` rows are gone).
- Endpoints (owner only): `GET /vehicles/{vehicle_id}/availability?start=&end=` → `list[SlotResponse(tanggal, status)]`; `POST /vehicles/{vehicle_id}/blocks` (`BlockRequest(dates: list[date] = Field(min_length=1))`) → 201; `DELETE /vehicles/{vehicle_id}/blocks/{tanggal}` → 204.

- [ ] **Step 1: Failing tests**: `test_lock_conflict_on_overlap` (lock 1–3 Dec for b1, lock 3–5 Dec for b2 → `Conflict` code `SLOT_UNAVAILABLE`, and no partial rows for b2); `test_release_only_own_booking` (b1 1–2 Dec, manual block 3 Dec; `release_slots(b1)` == 2 and the 3 Dec `DIBLOKIR` row remains); `test_block_and_unblock_api`; `test_unblock_booked_day_409`; `test_blocked_vehicle_ids_range`.
- [ ] **Step 2–4:** FAIL → implement → `pytest -v` PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(availability): unique slot lock, scoped release, manual block endpoints"`

---

### Task 9: Listing management (H9, BR-026, BR-027)

**Files:**
- Modify: `app/modules/listing/models.py` (drop `skor_kebasuan`; add `rental_id`, `biaya_tambahan: int`, `harga_all_in: int`, `status_publikasi: ListingStatus` default `DRAFT`, `created_at`, `updated_at`), `app/modules/listing/routers.py`
- Create: `app/modules/listing/schemas.py`, `app/modules/listing/service.py`
- Test: `tests/test_listing.py`; factory `make_listing(db, vehicle, status=ListingStatus.PUBLISHED, biaya_tambahan=0) -> Listing`

**Interfaces:**
- Consumes: `assert_vehicle_owner` (Task 7), `get_rental` (Task 6).
- Produces `listing/service.py`: `compute_all_in(tarif_dasar: int, biaya_tambahan: int) -> int` (sum); `is_stale(updated_at: datetime, now: datetime) -> bool` (`now - updated_at > listing_stale_days`); `get_published_listing(db, listing_id) -> Listing` (NotFound unless PUBLISHED).
- Endpoints: `POST /listings` (owner of vehicle; `ListingCreate(vehicle_id, judul, deskripsi: str | None, biaya_tambahan: int = Field(ge=0))` — **no `harga_all_in` in input**) → 201 `ListingResponse(id, vehicle_id, rental_id, judul, deskripsi, harga_all_in, status_publikasi, updated_at, is_stale)`. `PATCH /listings/{id}` (owner; recomputes price; bumps `updated_at`). `POST /listings/{id}/publish` → requires rental `LOLOS` (else 409 `RENTAL_NOT_VERIFIED`) and vehicle `AKTIF` (else 409 `VEHICLE_INACTIVE`). `GET /listings/{id}` public (PUBLISHED only). Remove the unpaginated `GET /listings` (search replaces it).

- [ ] **Step 1: Failing tests**: `test_penyewa_cannot_create` (403); `test_ghost_vehicle_404`; `test_price_computed` (tarif 300000 + biaya 50000 → harga_all_in 350000; body with `harga_all_in` → 422); `test_publish_requires_verified_rental` (rental MENUNGGU → 409 `RENTAL_NOT_VERIFIED`); `test_is_stale` (`updated_at` 8 days ago → `is_stale` True).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(listing): owner-only listings, server-computed all-in price, publish gate, freshness"`

---

### Task 10: Search with availability, location, sort, pagination

**Files:**
- Modify: `app/modules/search/routers.py`
- Create: `app/modules/search/schemas.py`
- Test: `tests/test_search.py`

**Interfaces:**
- Consumes: `blocked_vehicle_ids` (Task 8), `rental_ids_matching_location` (Task 6), `ListingResponse` (Task 9), `PageParams`/`Page` (Task 2).
- Endpoint: `GET /search` → `Page[ListingResponse]`. Query: `q: str | None` (judul ilike), `lokasi: str | None`, `jenis: str | None`, `min_price: int | None = Query(None, ge=0)`, `max_price: int | None = Query(None, ge=0)`, `start_date: date | None`, `end_date: date | None` (both or neither, else 422 `DATE_RANGE_INCOMPLETE`; `end_date < start_date` → 422 `DATE_RANGE_INVALID`), `sort: Literal["freshness","price_asc","price_desc"] = "freshness"` (freshness = `updated_at desc`). Only PUBLISHED listings of LOLOS rentals. Search reads `jenis` through the `vehicle` service (add `vehicle_ids_by_jenis(db, jenis) -> set[str]` to `vehicle/service.py`).

- [ ] **Step 1: Failing tests**: `test_excludes_booked_vehicle_in_range` (vehicle with slot 2 Dec excluded for 1–3 Dec, included for 4–5 Dec); `test_location_filter`; `test_sort_price_asc`; `test_pagination_meta` (25 listings, page_size=10, page=3 → 5 items, total_pages 3); `test_incomplete_range_422`.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(search): availability/location/jenis filters, sorting, pagination"`

---

### Task 11: eKYC verification hardening (H11)

**Files:**
- Modify: `app/modules/verification/models.py` (`ktp_path`, `selfie_path`, `status: VerificationStatus`, `alasan`, `reviewer_id`, `reviewed_at`; drop `data_ektp`), `app/modules/verification/routers.py`
- Create: `app/modules/verification/schemas.py`, `app/modules/verification/service.py`
- Test: `tests/test_verification.py`; factory `make_verified_user(db) -> User` (Penyewa with `TERVERIFIKASI` record)

**Interfaces:**
- Produces `VerificationService(db)` implementing `VerificationReadPort.get_status(user_id) -> VerificationStatus` (latest record; none → `MENUNGGU`… no: none → raise? Decision: none → `VerificationStatus.MENUNGGU`).
- Endpoints: `POST /verifications` (multipart `ktp`, `selfie`, auth) → 201 `VerificationResponse(id, status, created_at)`. Content type ∈ {`image/jpeg`, `image/png`} else 415 `UNSUPPORTED_MEDIA_TYPE`; size > `max_upload_bytes` → 413 `FILE_TOO_LARGE`; existing `MENUNGGU` or `TERVERIFIKASI` → 409 `VERIFICATION_EXISTS`. Files saved to `{upload_dir}/verifications/{new_id()}.{jpg|png}` (client filename never used), mode `0o600`, written via `await asyncio.to_thread(...)`. No fake OCR in response. `GET /verifications/me`. `GET /verifications?status=` (Admin, paginated). `POST /verifications/{id}/review` (Admin; `ReviewRequest(status: Literal[TERVERIFIKASI, DITOLAK], alasan: str | None)`) → audit `VERIFICATION_REVIEWED`, notify user.

- [ ] **Step 1: Failing tests**: `test_filename_ignored` (upload with filename `"../../evil.png"` → saved path is inside `tmp_path/verifications` and basename matches a UUID pattern; use `monkeypatch` on settings `upload_dir=tmp_path`); `test_rejects_pdf` (415); `test_rejects_large` (413 with `max_upload_bytes=10`); `test_second_submission_409`; `test_admin_review_sets_status` (then `VerificationService.get_status` == `TERVERIFIKASI`); `test_response_has_no_ocr` (`"ocr_result" not in r.json()`).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(verification): safe uploads, selfie stored, admin review flow, no fake OCR"`

---

### Task 12: Booking state machine (H5)

**Files:**
- Modify: `app/modules/booking/state.py` (rewrite; delete `process_payment_success`, `process_cancellation`)
- Test: `tests/test_booking_state.py` (replaces `test_booking.py`, `test_booking_lifecycle.py`)

**Interfaces:**
- Produces: `TRANSITIONS: dict[tuple[BookingState, BookingEvent], BookingState]` — exactly:

| From | Event | To |
|---|---|---|
| MENUNGGU_DP | DP_PAID | MENUNGGU_KONFIRMASI_RENTAL |
| MENUNGGU_DP | CANCEL / EXPIRE | DIBATALKAN |
| MENUNGGU_KONFIRMASI_RENTAL | CONFIRM | TERKONFIRMASI |
| MENUNGGU_KONFIRMASI_RENTAL | REJECT | DITOLAK |
| MENUNGGU_KONFIRMASI_RENTAL | CANCEL / SLA_BREACH | DIBATALKAN |
| TERKONFIRMASI | CANCEL | DIBATALKAN |
| TERKONFIRMASI | HANDOVER | BERJALAN |
| BERJALAN | RETURN | SELESAI |

- Produces: `transition(booking, event: BookingEvent) -> BookingState` — sets `booking.booking_state`, returns new state; pair not in table → `InvalidTransition(state, event)`. Pure (no DB, no escrow); guards like "escrow LUNAS before HANDOVER" live in the service (Task 17).

- [ ] **Step 1: Failing test** — parametrize over every `(state, event)` in `BookingState × BookingEvent`: if in `TRANSITIONS` assert result equals the table, else `pytest.raises(InvalidTransition)` and state unchanged. Plus `assert len(TRANSITIONS) == 10`.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(booking): explicit transition table, illegal transitions raise 409"`

---

### Task 13: Booking creation with server-side pricing (C1, H1, H4)

**Files:**
- Modify: `app/modules/booking/models.py` (columns below), `app/modules/booking/routers.py`
- Create: `app/modules/booking/schemas.py`, `app/modules/booking/pricing.py`, `app/modules/booking/service.py`
- Test: `tests/test_booking_create.py`, `tests/test_pricing.py`; factory `make_booking(db, penyewa, listing, state=..., **kw) -> Booking`

**Interfaces:**
- Booking columns: `id, user_id, rental_id, vehicle_id, listing_id, tanggal_mulai, tanggal_selesai, hari, harga_per_hari, subtotal, diskon, promo_id, total_nilai, dp, sisa` (all money `BigInteger`), `booking_state`, `escrow_state` (default `EscrowState.NONE`), `alasan_batal`, `dibatalkan_oleh`, `created_at`, `updated_at`, `dp_paid_at`, `confirmed_at`.
- Produces `pricing.py`: `@dataclass(frozen=True) Quote(hari, harga_per_hari, subtotal, diskon, total_nilai, dp, sisa)`; `quote(harga_per_hari: int, tanggal_mulai: date, tanggal_selesai: date, promo: Promo | None, dp_percent: float) -> Quote`. Rules: `hari = (selesai - mulai).days + 1`; `subtotal = harga_per_hari * hari`; `diskon = min(floor(subtotal * pct / 100), max_discount_amount)`; `total = subtotal - diskon`; `dp = ceil(total * dp_percent / 100)`; `sisa = total - dp`.
- Produces `booking/service.py`: `create_booking(db, user: CurrentUser, req: BookingCreate) -> Booking`; `get_booking(db, booking_id) -> Booking` (NotFound).
- Endpoint: `POST /bookings` (`BookingCreate(listing_id, tanggal_mulai, tanggal_selesai, promo_code: str | None = None)`) → 201 `BookingResponse` (all columns except internal `promo_id`). Checks in order: listing PUBLISHED (404); `tanggal_mulai >= today_wib()` else 422 `DATE_IN_PAST`; `selesai >= mulai` else 422 `DATE_RANGE_INVALID`; user verification `TERVERIFIKASI` else 403 `KYC_REQUIRED`; promo via `get_valid_promo` (422 `PROMO_INVALID`, never silently ignored); `lock_slots` (409 `SLOT_UNAVAILABLE`); audit `BOOKING_CREATED`. `rental_id`/`vehicle_id` come from the listing.

- [ ] **Step 1: Failing tests** (`tests/test_pricing.py` + `tests/test_booking_create.py`)

```python
def test_quote_single_day_and_rounding():
    q = quote(333_333, date(2026, 12, 1), date(2026, 12, 1), None, 30.0)
    assert (q.hari, q.subtotal, q.dp, q.dp + q.sisa) == (1, 333_333, 100_000, 333_333)

def test_quote_promo_capped():
    promo = Promo(discount_percent=50.0, max_discount_amount=100_000)
    q = quote(300_000, date(2026, 12, 1), date(2026, 12, 3), promo, 30.0)
    assert (q.subtotal, q.diskon, q.total_nilai) == (900_000, 100_000, 800_000)
```

API tests: `test_create_booking_201_server_priced` (client-sent `total_nilai` → 422 extra field; valid request → 201 with `total_nilai == harga_all_in * hari`, state `MENUNGGU_DP`); `test_requires_kyc` (403 `KYC_REQUIRED`); `test_past_date_422`; `test_reversed_dates_422`; `test_bad_promo_422`; `test_overlap_one_boundary_day_409_adjacent_ok` (existing 1–3 Dec; 3–5 Dec → 409 `SLOT_UNAVAILABLE`; 4–5 Dec → 201); `test_audit_booking_created`.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(booking): server-side pricing, KYC/date/promo validation, atomic slot lock (fixes POST /bookings 500)"`

---

### Task 14: Payments, webhook security, escrow ledger (C4)

**Files:**
- Modify: `app/modules/payment/models.py`, `app/modules/payment/routers.py`
- Create: `app/modules/payment/{schemas,service,escrow}.py`
- Test: `tests/test_payment.py`, `tests/test_escrow.py` (replace `test_payment_escrow.py`)

**Interfaces:**
- Models: `Payment(id, booking_id, type: PaymentType, order_id unique, amount: int, status: PaymentStatus, transaction_id unique nullable, created_at, paid_at)`. `EscrowLedger(id, booking_id, entry_type: LedgerEntryType, amount: int > 0, reference: str, created_at)` — insert-only.
- Produces `escrow.py`: `hold(db, booking_id, amount: int, reference: str) -> None`; `balance(db, booking_id) -> int` (`HOLD − RELEASE − REFUND`); `release(db, booking_id, reference: str) -> int` (releases full balance, returns amount, 0 → no row); `refund(db, booking_id, amount: int, reference: str) -> None` (amount > balance → `Conflict("REFUND_EXCEEDS_ESCROW", ...)`); `totals_for_bookings(db, booking_ids: list[str]) -> tuple[int, int]` (released, held); `EscrowReadService(db)` implementing `EscrowReadPort` (returns `booking.escrow_state` via `booking.service.get_booking`).
- Produces `payment/service.py`: `signature_for(order_id: str, status_code: str, gross_amount: str) -> str` = `sha512(order_id + status_code + gross_amount + settings.midtrans_server_key).hexdigest()`; `create_payment_intent(db, booking: Booking, type: PaymentType) -> Payment` (DP only when `MENUNGGU_DP`, amount `booking.dp`; PELUNASAN only when `TERKONFIRMASI`, amount `booking.sisa`; else 409 `PAYMENT_NOT_ALLOWED`; `order_id = f"{booking.id}-{type}"`; existing PENDING intent for same order returned); `handle_notification(db, payload: MidtransNotification) -> Payment`.
- `handle_notification` rules: bad signature → 401 `INVALID_SIGNATURE`; unknown `order_id` → 404; `int(float(gross_amount)) != payment.amount` → 422 `AMOUNT_MISMATCH`; payment already final → return it unchanged (idempotent); `transaction_status in {"settlement","capture"}` → `BERHASIL`, `{"expire","cancel","deny"}` → `GAGAL`, else stays `PENDING`. On BERHASIL: `escrow.hold`; DP + booking `MENUNGGU_DP` → `transition(DP_PAID)`, `escrow_state=DITAHAN_ESCROW`, `dp_paid_at=utcnow()`; DP + booking already `DIBATALKAN` → `RefundService.trigger_refund(full amount, "LATE_PAYMENT")` (Task 15 provides it; in this task call `escrow.refund` directly and switch in Task 15); PELUNASAN → `escrow_state=LUNAS`. Audit `PAYMENT_RECEIVED`; notify penyewa.
- Endpoints: `POST /bookings/{id}/payments` (owner; `PaymentIntentRequest(type: PaymentType)`) → 201 `PaymentIntentResponse(order_id, amount, type, status, redirect_url)` (`redirect_url = f"https://app.sandbox.midtrans.com/snap/v2/vtweb/{order_id}"`). `POST /payments/webhook` (no auth, signature required; body `MidtransNotification(order_id, status_code, gross_amount: str, signature_key, transaction_status, transaction_id)`; schema allows extra fields) → 200 `{"status": "ok"}`. `POST /payments/{order_id}/simulate` → only when `settings.env != "prod"` (else 404), builds a signed `settlement` payload and calls `handle_notification`.

- [ ] **Step 1: Failing tests**: `test_webhook_bad_signature_401`; `test_dp_settlement_moves_state` (state `MENUNGGU_KONFIRMASI_RENTAL`, `escrow.balance == dp`); `test_duplicate_notification_idempotent` (same payload twice → both 200, exactly one `HOLD` row); `test_amount_mismatch_422`; `test_late_dp_after_expiry_refunded` (booking `DIBATALKAN`, settlement arrives → state stays `DIBATALKAN`, balance 0, one `REFUND` row, no slots for booking); `test_pelunasan_only_when_confirmed` (intent on `MENUNGGU_DP` with type PELUNASAN → 409 `PAYMENT_NOT_ALLOWED`); `test_simulate_hidden_in_prod` (settings env `prod` → 404); `test_escrow_refund_overdraw` (hold 100, refund 150 → `Conflict` `REFUND_EXCEEDS_ESCROW`).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(payment): signed idempotent webhook, payment intents, append-only escrow ledger"`

---

### Task 15: Booking reads, cancellation, refund engine (C5, C6, H6, H7)

**Files:**
- Modify: `app/modules/refund/service.py`, `app/modules/refund/models.py` (`amount: int`, `reason`, ids), `app/modules/booking/{service,routers,schemas}.py`, `app/modules/payment/service.py` (late-DP path → `RefundService`)
- Test: `tests/test_refund.py` (replace), `tests/test_booking_cancel.py`, `tests/test_booking_read.py`

**Interfaces:**
- Produces `refund/service.py`: `calculate_refund_amount(paid_amount: int, tanggal_mulai: date, tanggal_batal: date) -> int` — `days = (mulai - batal).days`; `>= 2` → `paid_amount`; `== 1` → `paid_amount // 2`; else `0`. `RefundService(db)` implementing `RefundPort.trigger_refund(booking_id, amount, reason) -> str` (amount 0 → returns `""`, no row; else `escrow.refund` + `Refund` row, audit `REFUND_ISSUED`, returns refund id).
- Produces `booking/service.py`: `get_booking_for_actor(db, booking_id, actor: CurrentUser) -> Booking` (penyewa owner, staff of `booking.rental_id`, or Admin; else 403); `cancel_booking(db, booking: Booking, actor_id: str | None, alasan: str | None, by_rental: bool) -> Booking`. Order: `transition(CANCEL)` (raises before any side effect) → `release_slots` → refund amount = full escrow balance if `by_rental` else `calculate_refund_amount(balance, mulai, today_wib())` → `RefundService.trigger_refund` → `escrow.release` the remainder (reference `"CANCEL_FORFEIT"`) → `escrow_state = DIKEMBALIKAN` if refund > 0 else (`DICAIRKAN` if released > 0 else `NONE`) → audit `BOOKING_CANCELLED` → notify both parties.
- Endpoints: `GET /bookings` (penyewa own, `Page[BookingResponse]`, `?state=`); `GET /bookings/{id}`; `GET /rentals/me/bookings` (staff, `Page`, `?state=`); `POST /bookings/{id}/cancel` (body `CancelRequest(alasan: str | None = None)`; penyewa owner or rental staff; illegal state → 409 `INVALID_STATE_TRANSITION`) → `BookingResponse`.

- [ ] **Step 1: Failing tests**: `test_refund_tiers` (H-2 → 300000 of 300000; H-1 → 150000; H-0 → 0; uses **paid amount**, not total); `test_cancel_other_users_booking_403`; `test_cancel_selesai_409_slots_kept` (state SELESAI → 409, slot rows unchanged); `test_cancel_h0_after_dp_forfeits` (balance 0, one `RELEASE` row amount == dp, no `REFUND` row, slots deleted); `test_cancel_h2_full_refund` (Refund row amount == dp, `escrow_state == DIKEMBALIKAN`); `test_rental_cancel_always_full_refund`; `test_get_booking_access` (owner 200, rental staff 200, stranger 403); `test_alasan_in_body` (query param ignored, body stored in `alasan_batal`).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "fix(booking): owner-scoped cancel, tiered refund from escrow, scoped slot release, booking reads"`

---

### Task 16: Rental confirmation, rejection, background jobs (H2)

**Files:**
- Create: `app/jobs.py`
- Modify: `app/main.py` (lifespan starts/stops job loop; delete `cancel_expired_bookings`), `app/modules/booking/{service,routers}.py`
- Test: `tests/test_booking_confirm.py`, `tests/test_jobs.py`

**Interfaces:**
- Produces `booking/service.py`: `confirm_booking(db, booking, actor_id) -> Booking` (`CONFIRM`, `confirmed_at`, audit, notify); `reject_booking(db, booking, actor_id, alasan: str) -> Booking` (`REJECT`, release slots, full refund via `RefundService`, audit `BOOKING_REJECTED`); `expire_unpaid_bookings(db, now: datetime) -> int` (`MENUNGGU_DP` with `created_at < now - dp_expiry_minutes` → `EXPIRE` + release slots + audit `BOOKING_EXPIRED`); `breach_unconfirmed_bookings(db, now: datetime) -> int` (`MENUNGGU_KONFIRMASI_RENTAL` with `dp_paid_at < now - rental_confirm_sla_minutes` → `SLA_BREACH` + release + full refund + audit).
- Produces `app/jobs.py`: `async def run_jobs_once(session_factory) -> dict[str, int]` (each job in its own session/commit, exceptions logged via `logging.getLogger("driveo.jobs")` and not re-raised); `async def job_loop(session_factory, stop: asyncio.Event) -> None` (sleep `job_interval_seconds` between runs, exits on `stop`).
- Endpoints (staff of booking's rental): `POST /bookings/{id}/confirm` → `BookingResponse`; `POST /bookings/{id}/reject` (`RejectRequest(alasan: str = Field(min_length=3))`).

- [ ] **Step 1: Failing tests**: `test_confirm_by_staff` (state TERKONFIRMASI); `test_confirm_by_penyewa_403`; `test_confirm_twice_409`; `test_reject_full_refund_and_release`; `test_expire_releases_slots` (booking created 61 min ago → `expire_unpaid_bookings` returns 1, state DIBATALKAN, slots gone, a new booking on same dates → 201); `test_sla_breach_refunds` (dp_paid 121 min ago → DIBATALKAN, `Refund.amount == dp`); `test_job_failure_isolated` (monkeypatch `expire_unpaid_bookings` to raise → `run_jobs_once` still runs SLA job and returns).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(booking): rental confirm/reject, DP-expiry and SLA jobs that release slots and refund"`

---

### Task 17: Handover, return, escrow release (BR-007, BR-018)

**Files:**
- Create: `app/modules/booking/checklist_models.py` (`HandoverChecklist(id, booking_id, tipe: ChecklistType, odometer: int, bbm_persen: int, catatan, foto_urls: JSON list, created_by, created_at)`, unique `(booking_id, tipe)`)
- Modify: `app/modules/booking/{service,routers,schemas}.py`
- Test: `tests/test_booking_handover.py`

**Interfaces:**
- Produces: `handover_booking(db, booking, actor_id, checklist: ChecklistRequest) -> Booking` — requires `booking.escrow_state == EscrowState.LUNAS` else 409 `ESCROW_NOT_LUNAS`, then `HANDOVER`; `return_booking(db, booking, actor_id, checklist) -> Booking` — `RETURN`, `escrow.release(reference="TRIP_COMPLETED")`, `escrow_state = DICAIRKAN`, audit `BOOKING_COMPLETED` + `ESCROW_RELEASED`, notify penyewa to review.
- `ChecklistRequest(odometer: int = Field(ge=0), bbm_persen: int = Field(ge=0, le=100), catatan: str | None = None, foto_urls: list[str] = [])`.
- Endpoints (rental staff): `POST /bookings/{id}/handover`, `POST /bookings/{id}/return` → `BookingResponse`; `GET /bookings/{id}/checklists` (actor-scoped) → `list[ChecklistResponse]`.

- [ ] **Step 1: Failing tests**: `test_handover_blocked_until_lunas` (TERKONFIRMASI + DITAHAN_ESCROW → 409 `ESCROW_NOT_LUNAS`); `test_handover_after_pelunasan` (simulate PELUNASAN → handover 200, state BERJALAN); `test_return_completes_and_releases` (state SELESAI, `escrow.balance == 0`, `RELEASE` amount == total_nilai); `test_duplicate_handover_409`; `test_bbm_out_of_range_422`.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(booking): handover gated on LUNAS, return completes trip and releases escrow"`

---

### Task 18: Two-way reviews (BR-013)

**Files:**
- Modify: `app/modules/review/models.py` (`id, booking_id, author_id, author_role: UserRole, target_id, rating, komentar, created_at`, unique `(booking_id, author_role)`), `app/modules/review/routers.py`
- Create: `app/modules/review/schemas.py`, `app/modules/review/service.py`
- Test: `tests/test_reviews.py` (replace)

**Interfaces:**
- Consumes: `get_booking_for_actor` (Task 15).
- Endpoints: `POST /bookings/{id}/reviews` (`ReviewCreate(rating: int = Field(ge=1, le=5), komentar: str = Field(max_length=1000))`) → 201 `ReviewResponse`. Penyewa owner → `author_role=Penyewa`, `target_id=rental_id`; rental staff → `author_role=Rental`, `target_id=user_id`. Booking not `SELESAI` → 409 `BOOKING_NOT_COMPLETED`; second review by same side → 409 `REVIEW_EXISTS`. `GET /rentals/{id}/reviews` → `RentalReviewsResponse(average_rating: float | None, items: Page[ReviewResponse])`. Remove old `POST /reviews`.

- [ ] **Step 1: Failing tests**: `test_review_requires_selesai` (409); `test_rating_bounds` (0 and 6 → 422); `test_one_per_side` (penyewa twice → 409; rental once → 201); `test_stranger_403`; `test_rental_average` (ratings 4 and 5 → 4.5).
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(review): two-way reviews only after SELESAI, one per side, rental rating summary"`

---

### Task 19: Rental dashboard

**Files:**
- Modify: `app/modules/rental/{routers,schemas,service}.py`, `app/modules/booking/service.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `totals_for_bookings` (Task 14).
- Produces `booking/service.py`: `bookings_summary_for_rental(db, rental_id, today: date) -> tuple[dict[BookingState, int], list[str], list[Booking]]` (counts by state, all booking ids, `TERKONFIRMASI` bookings with `tanggal_mulai` within today..today+7 ordered ascending).
- Endpoint: `GET /rentals/me/dashboard` (staff) → `DashboardResponse(total_bookings: int, bookings_by_state: dict[str, int], pendapatan_dicairkan: int, escrow_ditahan: int, upcoming_handovers: list[BookingResponse])`.

- [ ] **Step 1: Failing test** `test_dashboard_numbers`: one SELESAI booking (released 900000), one TERKONFIRMASI starting in 3 days with DP 270000 held, one DIBATALKAN → `total_bookings 3`, `pendapatan_dicairkan 900000`, `escrow_ditahan 270000`, one upcoming handover; penyewa → 403.
- [ ] **Step 2–4:** FAIL → implement → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(rental): dashboard with booking stats, escrow totals, upcoming handovers"`

---

## Phase 2 — Persistence & End-to-End

### Task 20: PostgreSQL + Alembic migrations + referential integrity

**Files:**
- Create: `app/models.py` (imports every `models.py`), `alembic/versions/<rev>_initial_schema.py` (autogenerated), `tests/test_schema.py`
- Modify: all `models.py` (add `ForeignKey` on every `*_id` referencing its table: `users`, `roles`, `rentals`, `vehicles`, `listings`, `bookings`, `promos`, `membership_plans`, `verifications`; ondelete `RESTRICT`), `app/core/database.py` (SQLite `PRAGMA foreign_keys=ON` via `event.listens_for(engine.sync_engine, "connect")`), `alembic/env.py` (async engine from `get_settings().database_url`, `target_metadata = Base.metadata` after `import app.models`), `alembic.ini` (remove hardcoded URL), `app/main.py` (lifespan `create_all` only when `settings.env != "prod"`)

**Interfaces:**
- Produces: `app.models` import side-effect registers all tables. Prod startup expects `alembic upgrade head` to have run.

- [ ] **Step 1: Failing tests** (`tests/test_schema.py`)

```python
import app.models  # noqa
from app.core.database import Base

FK_COLUMNS = {("bookings", "user_id"), ("bookings", "listing_id"), ("vehicles", "rental_id"),
              ("listings", "vehicle_id"), ("payments", "booking_id"), ("escrow_ledgers", "booking_id"),
              ("vehicle_availability", "vehicle_id"), ("rental_staff", "user_id"), ("reviews", "booking_id")}

def test_foreign_keys_declared():
    for table, col in FK_COLUMNS:
        assert Base.metadata.tables[table].c[col].foreign_keys, f"{table}.{col} lacks FK"

async def test_orphan_booking_rejected(db):
    from app.modules.booking.models import Booking
    ...  # insert Booking with nonexistent listing_id → pytest.raises(IntegrityError) on commit
```

- [ ] **Step 2: Run** `pytest tests/test_schema.py -v` → FAIL.
- [ ] **Step 3: Implement**, then generate migration: `DRIVEO_DATABASE_URL=sqlite+aiosqlite:///./scratch_migrate.db alembic revision --autogenerate -m "initial schema"`; review the file (all tables, FKs, unique constraints `vehicle_availability(vehicle_id,tanggal)`, `payments.order_id`, `payments.transaction_id`, `reviews(booking_id,author_role)`, `checklists(booking_id,tipe)`, `vehicles.plat_nomor`).
- [ ] **Step 4: Verify** `rm -f scratch_migrate.db && DRIVEO_DATABASE_URL=sqlite+aiosqlite:///./scratch_migrate.db alembic upgrade head && alembic downgrade base` → exits 0; `rm scratch_migrate.db`; `pytest -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(db): foreign keys, alembic async env, initial migration, prod uses migrations"`

---

### Task 21: End-to-end flow, boundary guard, docs

**Files:**
- Create: `tests/test_e2e_flow.py`, `tests/test_boundaries.py`, `README.md`
- Modify: `tasks/todo.md` (reflect real status), remove leftover legacy tests and `app/mocks` imports from non-test code

**Interfaces:** consumes everything; produces none.

- [ ] **Step 1: Write the E2E test** — single test, HTTP only (except admin seeding via factory): register penyewa → admin approves eKYC → rental user onboards → admin verifies rental LOLOS → rental adds vehicle → creates & publishes listing → penyewa searches with dates (listing found) → books 3 days → DP intent + simulate → rental confirms → PELUNASAN intent + simulate → handover → return → penyewa reviews (201) → search same dates again excludes nothing (booking SELESAI keeps slots; assert listing absent) → dashboard `pendapatan_dicairkan == total_nilai`. Assert each step's status code and `booking_state`.
- [ ] **Step 2: Write the boundary test**

```python
import ast, pathlib
def test_no_cross_module_model_imports():
    root = pathlib.Path("app/modules")
    for f in root.rglob("*.py"):
        mod = f.relative_to(root).parts[0]
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.modules."):
                parts = node.module.split(".")
                if len(parts) >= 4 and parts[2] != mod and parts[3] in {"models", "checklist_models", "routers"}:
                    raise AssertionError(f"{f} imports {node.module}")

def test_mocks_not_used_in_app():
    for f in pathlib.Path("app").rglob("*.py"):
        if "mocks" not in f.parts:
            assert "app.mocks" not in f.read_text(), f
```

- [ ] **Step 3: Run** `pytest tests/test_e2e_flow.py tests/test_boundaries.py -v`; fix any boundary violations by routing through the owning module's `service.py` (expected offenders: `search`, `payment`, `booking`).
- [ ] **Step 4: Write `README.md`** — setup (`python -m venv venv`, `pip install -r requirements.txt`), required env vars (`DRIVEO_JWT_SECRET`, `DRIVEO_DATABASE_URL`, `DRIVEO_MIDTRANS_SERVER_KEY`, `DRIVEO_ENV`, `DRIVEO_SEED_ON_STARTUP`, `DRIVEO_SEED_ADMIN_PASSWORD`), `alembic upgrade head`, `uvicorn app.main:app --reload`, `pytest`, booking state diagram (table from Task 12), error envelope format. Update `tasks/todo.md` checkboxes to match reality.
- [ ] **Step 5: Run** `pytest -v` → all PASS, zero `DeprecationWarning` from `app/` (`pytest -W error::DeprecationWarning` on `app` modules).
- [ ] **Step 6: Commit** `git commit -m "test: end-to-end rental flow and module boundary guard; docs: README"`

---

## Out of Scope (explicitly deferred)

- Real Midtrans HTTP calls, real S3 storage, real OCR, real email/WhatsApp delivery (adapters remain DB-backed mocks).
- Encryption at rest for KTP images and payout accounts beyond file mode `0o600` / `ENCRYPTED_` placeholder — needs a KMS decision.
- Promo usage limits, rental staff invitations (`max_staff`), vehicle documents/photos upload.
- Rate limiting and account lockout on `/auth/login`.
