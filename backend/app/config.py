"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives at  backend/app/config.py
# parents[2]  resolves to the project root where .env lives
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Receipt Reader"
    app_version: str = "0.0.1"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/receipt_reader.db"

    # File storage
    upload_dir: Path = Path("data/uploads")
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_mime_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"]
    )

    # Google / Gemini
    google_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.0

    # xAI / Grok  (extractor_backend="grok" para usar durante desarrollo)
    xai_api_key: str = ""
    grok_model: str = "grok-4.5"

    # Selector de extractor: "gemini" | "grok"
    extractor_backend: str = "gemini"

    # Validation
    totals_tolerance_eur: float = 0.02
    line_tolerance_eur: float = 0.01

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:4173"]
    )


settings = Settings()
