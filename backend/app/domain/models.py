"""Domain layer — pure Python, no framework dependencies.

Imports allowed: stdlib, decimal, enum, datetime, dataclasses, typing.
NOT allowed: FastAPI, LangChain, LangGraph, SQLAlchemy, SQLite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4


class ReceiptStatus(StrEnum):
    """Lifecycle states of a receipt."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class ItemUnit(StrEnum):
    """Supported units of measure."""

    UNIT = "ud"
    KG = "kg"
    GRAM = "g"
    LITRE = "l"
    MILLILITRE = "ml"
    UNKNOWN = "unknown"


@dataclass
class DomainReceipt:
    """Core receipt aggregate root."""

    id: UUID
    filename: str
    file_path: str
    status: ReceiptStatus
    created_at: datetime
    updated_at: datetime
    commerce: str | None = None
    date: str | None = None          # ISO date string yyyy-mm-dd
    time: str | None = None          # HH:MM
    currency: str = "EUR"
    ticket_number: str | None = None
    payment_method: str | None = None
    error_message: str | None = None

    def can_process(self) -> bool:
        return self.status == ReceiptStatus.UPLOADED

    def can_confirm(self) -> bool:
        return self.status in (ReceiptStatus.EXTRACTED, ReceiptStatus.NEEDS_REVIEW)

    def transition_to(self, new_status: ReceiptStatus) -> None:
        allowed: dict[ReceiptStatus, set[ReceiptStatus]] = {
            ReceiptStatus.UPLOADED: {ReceiptStatus.PROCESSING},
            ReceiptStatus.PROCESSING: {
                ReceiptStatus.EXTRACTED,
                ReceiptStatus.NEEDS_REVIEW,
                ReceiptStatus.FAILED,
            },
            ReceiptStatus.EXTRACTED: {
                ReceiptStatus.NEEDS_REVIEW,
                ReceiptStatus.CONFIRMED,
            },
            ReceiptStatus.NEEDS_REVIEW: {ReceiptStatus.CONFIRMED},
            ReceiptStatus.CONFIRMED: set(),
            ReceiptStatus.FAILED: {ReceiptStatus.UPLOADED},
        }
        if new_status not in allowed.get(self.status, set()):
            raise ValueError(
                f"Invalid transition {self.status} -> {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC)


@dataclass
class DomainReceiptItem:
    """A single line item from a receipt."""

    id: UUID
    receipt_id: UUID
    raw_description: str
    normalized_description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    price_per_kg: Decimal | None = None
    discount: Decimal | None = None
    total_price: Decimal | None = None
    confidence: float | None = None
    needs_review: bool = False
    line_valid: bool | None = None
    line_difference: Decimal | None = None
    position: int = 0


@dataclass
class TaxDetail:
    """One tax bracket extracted from the receipt."""

    name: str | None = None      # e.g. "IVA 21%"
    rate: Decimal | None = None  # e.g. Decimal("0.21")
    base: Decimal | None = None
    amount: Decimal | None = None


@dataclass
class DomainReceiptTotals:
    """Totals section of a receipt."""

    id: UUID
    receipt_id: UUID
    subtotal: Decimal | None = None
    taxes: list[TaxDetail] = field(default_factory=list)
    total: Decimal | None = None
    calculated_total: Decimal | None = None
    difference: Decimal | None = None
    totals_valid: bool | None = None


@dataclass
class DomainExtractionJob:
    """Tracks one run of the extraction workflow."""

    id: UUID
    receipt_id: UUID
    started_at: datetime
    status: str = "pending"
    finished_at: datetime | None = None
    error: str | None = None
    model_name: str | None = None
    overall_confidence: float | None = None


@dataclass
class DomainReceiptReview:
    """Audit record when a human reviews/confirms a receipt."""

    id: UUID
    receipt_id: UUID
    reviewed_at: datetime
    corrections_json: str | None = None   # JSON snapshot of edits


def new_id() -> UUID:
    return uuid4()
