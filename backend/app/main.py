"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, receipts
from app.config import settings
from app.persistence.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database on startup."""
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Receipt Reader MVP — sube imágenes de tickets de supermercado españoles "
            "y extrae productos, cantidades, precios y totales con validación matemática."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(receipts.router)

    return app


app = create_app()
