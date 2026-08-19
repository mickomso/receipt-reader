"""LangGraph workflow nodes.

Each node receives and returns WorkflowState.
Nodes are pure functions — no FastAPI or HTTP dependencies.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from app.extraction.validator import run_validation
from app.workflow.base_extractor import BaseExtractor
from app.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


def load_receipt(state: WorkflowState) -> WorkflowState:
    """Verify the file exists and read its bytes."""
    file_path = state.get("file_path", "")
    path = Path(file_path)

    if not path.exists():
        return {**state, "status": "failed", "error": f"Fichero no encontrado: {file_path}"}

    try:
        image_bytes = path.read_bytes()
        # Infer MIME from extension
        suffix = path.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime = mime_map.get(suffix, "image/jpeg")
        return {**state, "image_bytes": image_bytes, "image_mime": mime, "status": "processing"}
    except OSError as exc:
        return {**state, "status": "failed", "error": str(exc)}


def normalize_image(state: WorkflowState) -> WorkflowState:
    """Basic image validation (size and format).  No transforms for MVP."""
    import io

    from PIL import Image

    image_bytes = state.get("image_bytes")
    if not image_bytes:
        return {**state, "status": "failed", "error": "Sin bytes de imagen"}

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return state
    except Exception as exc:
        return {**state, "status": "failed", "error": f"Imagen inválida: {exc}"}


def extract_receipt(state: WorkflowState, extractor: BaseExtractor) -> WorkflowState:
    """Call the LLM extractor and store raw extraction."""
    image_bytes = state.get("image_bytes")
    mime = state.get("image_mime", "image/jpeg")

    if not image_bytes:
        return {**state, "status": "failed", "error": "Sin imagen para extraer"}

    try:
        extraction = extractor.extract(image_bytes, mime)
        return {
            **state,
            "extraction": extraction.model_dump(mode="json"),
            "overall_confidence": extraction.overall_confidence,
        }
    except Exception as exc:
        logger.exception("Extraction failed")
        return {**state, "status": "failed", "error": f"Error de extracción: {exc}"}


def validate_extraction(state: WorkflowState) -> WorkflowState:
    """Run mathematical validation on extracted items."""
    from app.extraction.schemas import ReceiptExtractionSchema

    extraction_dict = state.get("extraction")
    if not extraction_dict:
        return {**state, "status": "failed", "error": "Sin datos de extracción para validar"}

    try:
        extraction = ReceiptExtractionSchema.model_validate(extraction_dict)
        report = run_validation(extraction)
        return {
            **state,
            "validation_report": {
                "lines": [
                    {
                        "position": lr.position,
                        "raw_description": lr.raw_description,
                        "expected": str(lr.expected) if lr.expected is not None else None,
                        "declared": str(lr.declared) if lr.declared is not None else None,
                        "difference": str(lr.difference) if lr.difference is not None else None,
                        "valid": lr.valid,
                        "reason": lr.reason,
                    }
                    for lr in report.lines
                ],
                "totals": {
                    "declared_total": str(report.totals.declared_total) if report.totals.declared_total is not None else None,
                    "calculated_total": str(report.totals.calculated_total) if report.totals.calculated_total is not None else None,
                    "difference": str(report.totals.difference) if report.totals.difference is not None else None,
                    "valid": report.totals.valid,
                    "reason": report.totals.reason,
                },
                "overall_valid": report.overall_valid,
                "needs_review": report.needs_review,
            },
            "needs_review": report.needs_review or extraction.needs_review,
        }
    except Exception as exc:
        logger.exception("Validation error")
        return {**state, "status": "failed", "error": f"Error de validación: {exc}"}


def validate_totals(state: WorkflowState) -> WorkflowState:
    """Verify totals validation result is captured (already done in validate_extraction)."""
    report = state.get("validation_report", {})
    totals = report.get("totals", {}) if report else {}
    if totals.get("valid") is False:
        logger.warning(
            "Totals mismatch: declared=%s calculated=%s diff=%s",
            totals.get("declared_total"),
            totals.get("calculated_total"),
            totals.get("difference"),
        )
    return state


def route_result(state: WorkflowState) -> WorkflowState:
    """Determine final status: extracted or needs_review."""
    if state.get("status") == "failed":
        return state

    needs_review = state.get("needs_review", False)
    extraction_dict = state.get("extraction", {})
    if extraction_dict and extraction_dict.get("needs_review"):
        needs_review = True

    new_status = "needs_review" if needs_review else "extracted"
    return {**state, "status": new_status}


def persist_result(state: WorkflowState, repository) -> WorkflowState:
    """Save extraction results to the database."""
    from app.domain.models import ReceiptStatus
    from app.extraction.schemas import ReceiptExtractionSchema
    from app.extraction.validator import (
        LineValidationResult,
        TotalsValidationResult,
        ValidationReport,
    )

    receipt_id = state.get("receipt_id", "")
    extraction_dict = state.get("extraction")
    report_dict = state.get("validation_report")
    status_str = state.get("status", "failed")

    try:
        status = ReceiptStatus(status_str)
    except ValueError:
        status = ReceiptStatus.FAILED

    if extraction_dict and report_dict:
        extraction = ReceiptExtractionSchema.model_validate(extraction_dict)

        # Rebuild ValidationReport from serialised dict
        lines = [
            LineValidationResult(
                position=ln["position"],
                raw_description=ln["raw_description"],
                expected=Decimal(ln["expected"]) if ln["expected"] else None,
                declared=Decimal(ln["declared"]) if ln["declared"] else None,
                difference=Decimal(ln["difference"]) if ln["difference"] else None,
                valid=ln["valid"],
                reason=ln["reason"],
            )
            for ln in report_dict.get("lines", [])
        ]
        td = report_dict.get("totals", {})
        totals_result = TotalsValidationResult(
            declared_total=Decimal(td["declared_total"]) if td.get("declared_total") else None,
            calculated_total=Decimal(td["calculated_total"]) if td.get("calculated_total") else None,
            difference=Decimal(td["difference"]) if td.get("difference") else None,
            valid=td.get("valid"),
            reason=td.get("reason", ""),
        )
        report = ValidationReport(
            lines=lines,
            totals=totals_result,
            overall_valid=report_dict.get("overall_valid"),
            needs_review=report_dict.get("needs_review", False),
        )

        repository.save_extraction(receipt_id, extraction, report)

    repository.update_status(receipt_id, status)

    if state.get("job_id"):
        error = state.get("error") if status == ReceiptStatus.FAILED else None
        confidence = state.get("overall_confidence")
        repository.finish_job(
            state["job_id"],
            status="completed" if status != ReceiptStatus.FAILED else "failed",
            error=error,
            confidence=confidence,
        )

    return {**state, "status": status_str}
