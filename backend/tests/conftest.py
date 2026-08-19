"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Use in-memory SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_receipt_reader.db")
os.environ.setdefault("UPLOAD_DIR", "/tmp/test_receipt_uploads")
os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-tests")

from app.api.deps import get_extractor
from app.main import create_app
from app.persistence.database import Base, get_db
from tests.fixtures.fake_extractor import FakeExtractor


@pytest.fixture(scope="session")
def test_upload_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("uploads")
    return d


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_extractor() -> FakeExtractor:
    return FakeExtractor()


@pytest.fixture
def app(db_engine, test_upload_dir, fake_extractor):
    """FastAPI test app with overridden DB and extractor dependencies."""
    from app.config import settings

    settings.upload_dir = test_upload_dir

    application = create_app()

    # Override DB dependency
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def override_get_extractor():
        return fake_extractor

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_extractor] = override_get_extractor

    return application


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
