"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _ensure_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        db_path = Path(url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Session:  # type: ignore[return]
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    # Import ORM models to register them before create_all
    from app.persistence import orm_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
