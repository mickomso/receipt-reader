"""LangGraph workflow state definition."""

from __future__ import annotations

from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    """Shared state passed through all LangGraph nodes."""

    receipt_id: str
    file_path: str
    image_bytes: bytes | None
    image_mime: str | None
    extraction: dict | None        # ReceiptExtractionSchema as dict
    validation_report: dict | None # ValidationReport serialised
    status: str                        # maps to ReceiptStatus
    error: str | None
    needs_review: bool
    overall_confidence: float | None
    job_id: str | None
