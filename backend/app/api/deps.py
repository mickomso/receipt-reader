"""FastAPI dependencies (dependency injection)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.persistence.database import get_db
from app.services.receipt_service import ReceiptService
from app.workflow.base_extractor import BaseExtractor


@lru_cache(maxsize=1)
def get_extractor() -> BaseExtractor:
    """Create the extractor once.  Backend selected by EXTRACTOR_BACKEND env var.
    Swap in tests via dependency override."""
    if settings.extractor_backend == "grok":
        from app.workflow.grok_extractor import GrokExtractor

        return GrokExtractor()

    from app.workflow.llm_extractor import LLMExtractor

    return LLMExtractor()


def get_receipt_service(
    db: Session = Depends(get_db),
    extractor: BaseExtractor = Depends(get_extractor),
) -> ReceiptService:
    return ReceiptService(db, extractor)
