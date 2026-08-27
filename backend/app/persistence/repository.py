"""Repository pattern for receipt persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models import (
    DomainReceipt,
    DomainReceiptItem,
    DomainReceiptTotals,
    ReceiptStatus,
    TaxDetail,
)
from app.extraction.schemas import ReceiptExtractionSchema
from app.extraction.validator import ValidationReport
from app.persistence.orm_models import (
    ExtractionJobORM,
    ReceiptItemORM,
    ReceiptORM,
    ReceiptReviewORM,
    ReceiptTotalsORM,
    TaxDetailORM,
)


def _d(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


# ---------------------------------------------------------------------------
# Mappers ORM → Domain
# ---------------------------------------------------------------------------

def _receipt_to_domain(orm: ReceiptORM) -> DomainReceipt:
    return DomainReceipt(
        id=UUID(orm.id),
        filename=orm.filename,
        file_path=orm.file_path,
        status=ReceiptStatus(orm.status),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        commerce=orm.commerce,
        date=orm.date,
        time=orm.time,
        currency=orm.currency,
        ticket_number=orm.ticket_number,
        payment_method=orm.payment_method,
        error_message=orm.error_message,
    )


def _item_to_domain(orm: ReceiptItemORM) -> DomainReceiptItem:
    return DomainReceiptItem(
        id=UUID(orm.id),
        receipt_id=UUID(orm.receipt_id),
        raw_description=orm.raw_description,
        normalized_description=orm.normalized_description,
        quantity=_d(orm.quantity),
        unit=orm.unit,
        unit_price=_d(orm.unit_price),
        price_per_kg=_d(orm.price_per_kg),
        discount=_d(orm.discount),
        total_price=_d(orm.total_price),
        confidence=orm.confidence,
        needs_review=orm.needs_review,
        line_valid=orm.line_valid,
        line_difference=_d(orm.line_difference),
        position=orm.position,
    )


def _totals_to_domain(orm: ReceiptTotalsORM) -> DomainReceiptTotals:
    taxes = [
        TaxDetail(
            name=t.name,
            rate=_d(t.rate),
            base=_d(t.base),
            amount=_d(t.amount),
        )
        for t in orm.taxes
    ]
    return DomainReceiptTotals(
        id=UUID(orm.id),
        receipt_id=UUID(orm.receipt_id),
        subtotal=_d(orm.subtotal),
        taxes=taxes,
        total=_d(orm.total),
        calculated_total=_d(orm.calculated_total),
        difference=_d(orm.difference),
        totals_valid=orm.totals_valid,
    )


# ---------------------------------------------------------------------------
# Receipt repository
# ---------------------------------------------------------------------------

class ReceiptRepository:

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, filename: str, file_path: str) -> DomainReceipt:
        orm = ReceiptORM(filename=filename, file_path=file_path, status="uploaded")
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return _receipt_to_domain(orm)

    def get(self, receipt_id: str) -> DomainReceipt | None:
        orm = self._db.get(ReceiptORM, receipt_id)
        return _receipt_to_domain(orm) if orm else None

    def delete(self, receipt_id: str) -> DomainReceipt | None:
        orm = self._db.get(ReceiptORM, receipt_id)
        if not orm:
            return None
        receipt = _receipt_to_domain(orm)
        self._db.delete(orm)
        self._db.commit()
        return receipt

    def list_all(self, skip: int = 0, limit: int = 50) -> list[DomainReceipt]:
        rows = (
            self._db.query(ReceiptORM)
            .order_by(ReceiptORM.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_receipt_to_domain(r) for r in rows]

    def update_status(self, receipt_id: str, status: ReceiptStatus) -> DomainReceipt | None:
        orm = self._db.get(ReceiptORM, receipt_id)
        if not orm:
            return None
        orm.status = status.value
        orm.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(orm)
        return _receipt_to_domain(orm)

    def update_fields(self, receipt_id: str, **fields) -> DomainReceipt | None:
        orm = self._db.get(ReceiptORM, receipt_id)
        if not orm:
            return None
        for k, v in fields.items():
            setattr(orm, k, v)
        orm.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(orm)
        return _receipt_to_domain(orm)

    def get_items(self, receipt_id: str) -> list[DomainReceiptItem]:
        rows = (
            self._db.query(ReceiptItemORM)
            .filter(ReceiptItemORM.receipt_id == receipt_id)
            .order_by(ReceiptItemORM.position)
            .all()
        )
        return [_item_to_domain(r) for r in rows]

    def get_totals(self, receipt_id: str) -> DomainReceiptTotals | None:
        orm = (
            self._db.query(ReceiptTotalsORM)
            .filter(ReceiptTotalsORM.receipt_id == receipt_id)
            .first()
        )
        return _totals_to_domain(orm) if orm else None

    def save_extraction(
        self,
        receipt_id: str,
        extraction: ReceiptExtractionSchema,
        report: ValidationReport,
    ) -> None:
        """Persist extraction results and validation report atomically."""
        # Delete old items and totals
        self._db.query(ReceiptItemORM).filter(
            ReceiptItemORM.receipt_id == receipt_id
        ).delete()
        old_totals = (
            self._db.query(ReceiptTotalsORM)
            .filter(ReceiptTotalsORM.receipt_id == receipt_id)
            .first()
        )
        if old_totals:
            self._db.delete(old_totals)
        self._db.flush()

        # Insert new items
        line_map = {lr.position: lr for lr in report.lines}
        for pos, item in enumerate(extraction.items):
            lr = line_map.get(pos)
            item_orm = ReceiptItemORM(
                receipt_id=receipt_id,
                position=pos,
                raw_description=item.raw_description,
                normalized_description=item.normalized_description,
                quantity=float(item.quantity) if item.quantity is not None else None,
                unit=item.unit,
                unit_price=float(item.unit_price) if item.unit_price is not None else None,
                price_per_kg=float(item.price_per_kg) if item.price_per_kg is not None else None,
                discount=float(item.discount) if item.discount is not None else None,
                total_price=float(item.total_price) if item.total_price is not None else None,
                confidence=item.confidence,
                needs_review=item.needs_review,
                line_valid=lr.valid if lr else None,
                line_difference=float(lr.difference) if lr and lr.difference is not None else None,
            )
            self._db.add(item_orm)

        # Insert totals
        totals_orm = ReceiptTotalsORM(
            receipt_id=receipt_id,
            subtotal=float(extraction.subtotal) if extraction.subtotal is not None else None,
            total=float(extraction.total) if extraction.total is not None else None,
            calculated_total=(
                float(report.totals.calculated_total)
                if report.totals.calculated_total is not None
                else None
            ),
            difference=(
                float(report.totals.difference)
                if report.totals.difference is not None
                else None
            ),
            totals_valid=report.totals.valid,
        )
        self._db.add(totals_orm)
        self._db.flush()

        # Insert taxes
        for tax in extraction.taxes:
            self._db.add(
                TaxDetailORM(
                    totals_id=totals_orm.id,
                    name=tax.name,
                    rate=float(tax.rate) if tax.rate is not None else None,
                    base=float(tax.base) if tax.base is not None else None,
                    amount=float(tax.amount) if tax.amount is not None else None,
                )
            )

        # Update receipt header
        orm = self._db.get(ReceiptORM, receipt_id)
        if orm:
            orm.commerce = extraction.commerce
            orm.date = extraction.date
            orm.time = extraction.time
            orm.currency = extraction.currency
            orm.ticket_number = extraction.ticket_number
            orm.payment_method = extraction.payment_method
            orm.updated_at = datetime.now(UTC)

        self._db.commit()

    def save_review(self, receipt_id: str, corrections_json: str | None = None) -> None:
        review = ReceiptReviewORM(
            receipt_id=receipt_id,
            reviewed_at=datetime.now(UTC),
            corrections_json=corrections_json,
        )
        self._db.add(review)
        self._db.commit()

    def save_job(self, job_orm: ExtractionJobORM) -> None:
        self._db.add(job_orm)
        self._db.commit()
        self._db.refresh(job_orm)

    def finish_job(
        self,
        job_id: str,
        status: str,
        error: str | None = None,
        confidence: float | None = None,
    ) -> None:
        orm = self._db.get(ExtractionJobORM, job_id)
        if orm:
            orm.finished_at = datetime.now(UTC)
            orm.status = status
            orm.error = error
            orm.overall_confidence = confidence
            self._db.commit()
