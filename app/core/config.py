from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: Literal["dev", "demo", "prod"] = "dev"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    database_url: str = "sqlite+aiosqlite:///:memory:"
    cors_origins: list[str] = ["http://localhost:3000"]
    dp_percent: float = 30.0
    dp_expiry_minutes: int = 60
    rental_confirm_sla_minutes: int = 120
    listing_stale_days: int = 7
    default_max_vehicles: int = 5
    upload_dir: str = "uploads"
    max_upload_bytes: int = 5_000_000
    midtrans_server_key: str = "dev-server-key"
    job_interval_seconds: int = 60
    seed_on_startup: bool = False
    seed_admin_password: str | None = None

    model_config = SettingsConfigDict(env_prefix="DRIVEO_", env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
