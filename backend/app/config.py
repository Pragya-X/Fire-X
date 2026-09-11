"""FIRE-X configuration. All values can be overridden via environment / .env."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), extra="ignore")

    # Core
    APP_NAME: str = "FIRE-X"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    # Database: SQLite by default; Postgres/PostGIS when DATABASE_URL is set
    DATABASE_URL: str = "sqlite:///./firex.db"

    # Auth
    JWT_SECRET: str = "firex-dev-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 12

    # Google OAuth (optional - demo SSO fallback when unset)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"

    # Providers (all optional - fall back to demo mode when unset)
    FIRMS_API_KEY: str = ""
    FIRMS_MAP_KEY: str = ""
    SATELLITE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    FIRMS_API_URL: str = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    # Email / SMTP (Gmail app password works). All optional - console fallback otherwise.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    MAIL_FROM_NAME: str = "FIRE-X"
    # Recipient(s) for operational alerts (comma-separated); defaults to the acting user's email
    MAIL_ALERT_RECIPIENTS: str = ""

    REFERENCE_BUNDLE_PATH: str = ""  # Explicit real reference bundle for legacy live ingestion.
    EVENT_MODEL_PATH: str = ""  # Trusted operator-approved event artifact; empty keeps evidence rules.
    ML_MODE: Literal["rules", "demo", "trained"] = "rules"
    ML_FALLBACK_MODE: Literal["rules", "demo"] = "rules"

    # Storage
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MODEL_DIR: str = str(BASE_DIR.parent / "ml" / "models")
    DATA_DIR: str = str(BASE_DIR.parent / "data")

    # CORS
    CORS_ORIGINS: str = "*"

    # Demo
    DEMO_MODE: bool = True

    # Auto-sync: run the FIRMS ingest on a server-side 2-minute schedule.
    FIRMS_AUTO_SYNC: bool = True

    # Tuning
    AUTO_ALERT_RISK_THRESHOLD: int = 80

    @model_validator(mode="after")
    def production_configuration(self):
        if self.ENV == "production":
            problems = []
            if self.DEBUG or self.DEMO_MODE:
                problems.append("DEBUG and DEMO_MODE must be false")
            if len(self.JWT_SECRET) < 32 or any(word in self.JWT_SECRET.lower() for word in ("change-me", "dev-secret", "docker-secret")):
                problems.append("a unique JWT_SECRET of at least 32 characters is required")
            if not self.cors_origin_list or "*" in self.cors_origin_list or any(not o.startswith("https://") for o in self.cors_origin_list):
                problems.append("explicit HTTPS CORS origins are required")
            if not self.is_postgres:
                problems.append("PostgreSQL/PostGIS is required")
            if self.GOOGLE_CLIENT_ID or self.GOOGLE_CLIENT_SECRET:
                problems.append("Google OAuth is disabled in production pending state/PKCE and token transport hardening")
            if problems:
                raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgres") or self.DATABASE_URL.startswith("postgresql")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def firms_api_key(self) -> Optional[str]:
        return self.FIRMS_API_KEY.strip() or self.FIRMS_MAP_KEY.strip() or None

    @property
    def google_redirect_uri(self) -> str:
        return self.GOOGLE_REDIRECT_URI.strip() or "http://localhost:8000/api/v1/auth/google/callback"

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST.strip() and self.SMTP_USER.strip())

    @property
    def mail_from(self) -> str:
        return self.SMTP_FROM.strip() or self.SMTP_USER.strip() or "firex@localhost"

    @property
    def alert_recipients(self) -> list[str]:
        if self.MAIL_ALERT_RECIPIENTS.strip():
            return [e.strip() for e in self.MAIL_ALERT_RECIPIENTS.split(",") if e.strip()]
        return []

    @property
    def openai_api_key(self) -> Optional[str]:
        return self.OPENAI_API_KEY.strip() or None


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)
