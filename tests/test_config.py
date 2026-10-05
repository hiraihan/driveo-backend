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
