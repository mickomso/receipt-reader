"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(tags=["health"])


class HealthOut(BaseModel):
    status: str
    version: str
    app: str


@router.get("/health", response_model=HealthOut, summary="Health check")
def health() -> HealthOut:
    """Returns application health status."""
    return HealthOut(status="ok", version=settings.app_version, app=settings.app_name)
