"""Centralized, env-driven configuration for saber-football.

This module intentionally uses only the standard library so tests and lightweight
metadata checks can run before the full analytics environment is installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv(path: Path | None = None) -> None:
    """Load repo-local .env values without overriding the process environment."""
    env_path = path or Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings, validated lightly and typed."""

    env: str = os.getenv("SABER_ENV", "dev")
    storage_backend: str = os.getenv("SABER_STORAGE_BACKEND", "local")
    data_dir: Path = Path(os.getenv("SABER_DATA_DIR", "./data"))

    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = _env_int("POSTGRES_PORT", 5432)
    postgres_user: str = os.getenv("POSTGRES_USER", "saber")
    postgres_password: str = (
        os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PWD") or "change-me"
    )
    postgres_db: str = os.getenv("POSTGRES_DB", "saber_football")

    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "saber")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "change-me")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "football-sabermetrics")
    minio_prefix: str = os.getenv("MINIO_PREFIX", "").strip("/")

    cfbd_api_key: str = os.getenv("CFBD_API_KEY", "")

    nflverse_rpm: int = _env_int("SABER_NFLVERSE_RPM", 60)
    cfbd_rpm: int = _env_int("SABER_CFBD_RPM", 30)
    pfr_rpm: int = _env_int("SABER_PFR_RPM", 18)
    http_cache_ttl_days: int = _env_int("SABER_HTTP_CACHE_TTL_DAYS", 7)
    user_agent: str = os.getenv(
        "SABER_USER_AGENT",
        "savepoint-football-sabermetrics/0.1 (contact: alex@savepointanalytics.com)",
    )

    @property
    def postgres_url(self) -> str:
        """SQLAlchemy/psycopg connection URL for the curated warehouse."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def bronze_root(self) -> str:
        """Root URI for the bronze/raw landing zone."""
        if self.storage_backend == "minio":
            prefix = f"/{self.minio_prefix}" if self.minio_prefix else ""
            return f"s3://{self.minio_bucket}{prefix}"
        return str((self.data_dir / "bronze").resolve())

    @property
    def cache_dir(self) -> Path:
        """On-disk HTTP cache directory."""
        return (self.data_dir / "cache").resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


settings = get_settings()
