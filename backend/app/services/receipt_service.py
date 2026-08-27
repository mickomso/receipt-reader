"""Receipt application service — orchestrates workflow and repository."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domain.models import DomainReceipt, DomainReceiptItem, DomainReceiptTotals, ReceiptStatus
from app.persistence.orm_models import ExtractionJobORM
from app.persistence.repository import ReceiptRepository
from app.workflow.base_extractor import BaseExtractor
from app.workflow.graph import run_workflow

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, db: Session, extractor: BaseExtractor) -> None:
        self._repo = ReceiptRepository(db)
        self._extractor = extractor

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_receipt(self, filename: str, file_path: str) -> DomainReceipt:
        return self._repo.create(filename, file_path)

    def get_receipt(self, receipt_id: str) -> DomainReceipt | None:
        return self._repo.get(receipt_id)

    def delete_receipt(self, receipt_id: str) -> DomainReceipt | None:
        receipt = self._repo.delete(receipt_id)
        if receipt:
            Path(receipt.file_path).unlink(missing_ok=True)
        return receipt

    def list_receipts(self, skip: int = 0, limit: int = 50) -> list[DomainReceipt]:
        return self._repo.list_all(skip, limit)

    def get_items(self, receipt_id: str) -> list[DomainReceiptItem]:
        return self._repo.get_items(receipt_id)

    def get_totals(self, receipt_id: str) -> DomainReceiptTotals | None:
        return self._repo.get_totals(receipt_id)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_receipt(self, receipt_id: str) -> DomainReceipt:
        """Run the full extraction workflow synchronously."""
        receipt = self._repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} no encontrado")

        if not receipt.can_process():
            raise ValueError(
                f"No se puede procesar un ticket en estado '{receipt.status}'. "
                "Solo se pueden procesar tickets en estado 'uploaded'."
            )

        # Create job record
        job = ExtractionJobORM(
            id=str(uuid4()),
            receipt_id=receipt_id,
            started_at=datetime.now(UTC),
            status="running",
            model_name="gemini",
        )
        self._repo.save_job(job)

        # Transition to processing
        self._repo.update_status(receipt_id, ReceiptStatus.PROCESSING)

        try:
            run_workflow(
                receipt_id=receipt_id,
                file_path=receipt.file_path,
                job_id=job.id,
                extractor=self._extractor,
                repository=self._repo,
            )
        except Exception as exc:
            logger.exception("Workflow crashed for receipt %s", receipt_id)
            self._repo.update_fields(receipt_id, error_message=str(exc))
            self._repo.update_status(receipt_id, ReceiptStatus.FAILED)
            self._repo.finish_job(job.id, "failed", error=str(exc))
            raise

        updated = self._repo.get(receipt_id)
        return updated

    # ------------------------------------------------------------------
    # Review and confirmation
    # ------------------------------------------------------------------

    def patch_receipt(self, receipt_id: str, patch: dict) -> DomainReceipt | None:
        """Apply partial updates to receipt header fields."""
        allowed_fields = {"commerce", "date", "time", "currency", "ticket_number", "payment_method"}
        safe_patch = {k: v for k, v in patch.items() if k in allowed_fields}
        if not safe_patch:
            return self._repo.get(receipt_id)
        return self._repo.update_fields(receipt_id, **safe_patch)

    def confirm_receipt(self, receipt_id: str, corrections_json: str | None = None) -> DomainReceipt:
        receipt = self._repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} no encontrado")
        if not receipt.can_confirm():
            raise ValueError(
                f"No se puede confirmar un ticket en estado '{receipt.status}'. "
                "Solo se pueden confirmar tickets en estado 'extracted' o 'needs_review'."
            )
        self._repo.save_review(receipt_id, corrections_json)
        self._repo.update_status(receipt_id, ReceiptStatus.CONFIRMED)
        return self._repo.get(receipt_id)
