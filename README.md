# DriveO Backend

Backend service for DriveO vehicle rental platform.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Required variables:
- `DRIVEO_JWT_SECRET`: 32+ character secret string for JWT signing
- `DRIVEO_DATABASE_URL`: Database connection URL (e.g. `sqlite+aiosqlite:///./dev.db` for dev, `postgresql+asyncpg://user:pass@host/db` for prod)
- `DRIVEO_MIDTRANS_SERVER_KEY`: Server key for Midtrans payment gateway
- `DRIVEO_ENV`: Environment (`dev`, `demo`, or `prod`)

Optional:
- `DRIVEO_SEED_ON_STARTUP`: Boolean to run seed script on startup
- `DRIVEO_SEED_ADMIN_PASSWORD`: Password for the default admin user

## Database Migrations

Run Alembic to upgrade the database schema:

```bash
alembic upgrade head
```

## Running the Server

```bash
uvicorn app.main:app --reload
```

## Running Tests

```bash
pytest
```

## Booking State Machine

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

## Error Envelope Format

All errors follow a unified structure:

```json
{
  "error": {
    "code": "ERROR_CODE_IN_UPPER_SNAKE",
    "message": "Pesan error dalam Bahasa Indonesia",
    "details": null
  }
}
```
