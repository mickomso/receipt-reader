"""SQLAlchemy ORM models.  Maps domain entities to SQLite tables."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.database import Base


def _uuid() -> str:
    return str(uuid4())


class ReceiptORM(Base):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    commerce: Mapped[str | None] = mapped_column(String(255))
    date: Mapped[str | None] = mapped_column(String(10))
    time: Mapped[str | None] = mapped_column(String(8))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    ticket_number: Mapped[str | None] = mapped_column(String(64))
    payment_method: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    items: Mapped[list[ReceiptItemORM]] = relationship(
        "ReceiptItemORM", back_populates="receipt", cascade="all, delete-orphan"
    )
    totals: Mapped[ReceiptTotalsORM | None] = relationship(
        "ReceiptTotalsORM", back_populates="receipt", uselist=False, cascade="all, delete-orphan"
    )
    jobs: Mapped[list[ExtractionJobORM]] = relationship(
        "ExtractionJobORM", back_populates="receipt", cascade="all, delete-orphan"
    )
    reviews: Mapped[list[ReceiptReviewORM]] = relationship(
        "ReceiptReviewORM", back_populates="receipt", cascade="all, delete-orphan"
    )


class ReceiptItemORM(Base):
    __tablename__ = "receipt_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    receipt_id: Mapped[str] = mapped_column(String(36), ForeignKey("receipts.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 4))
    unit: Mapped[str | None] = mapped_column(String(16))
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 4))
    price_per_kg: Mapped[float | None] = mapped_column(Numeric(12, 4))
    discount: Mapped[float | None] = mapped_column(Numeric(12, 4))
    total_price: Mapped[float | None] = mapped_column(Numeric(12, 4))
    confidence: Mapped[float | None] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    line_valid: Mapped[bool | None] = mapped_column(Boolean)
    line_difference: Mapped[float | None] = mapped_column(Numeric(12, 4))

    receipt: Mapped[ReceiptORM] = relationship("ReceiptORM", back_populates="items")


class TaxDetailORM(Base):
    __tablename__ = "tax_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    totals_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("receipt_totals.id"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(64))
    rate: Mapped[float | None] = mapped_column(Numeric(6, 4))
    base: Mapped[float | None] = mapped_column(Numeric(12, 4))
    amount: Mapped[float | None] = mapped_column(Numeric(12, 4))

    totals: Mapped[ReceiptTotalsORM] = relationship("ReceiptTotalsORM", back_populates="taxes")


class ReceiptTotalsORM(Base):
    __tablename__ = "receipt_totals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    receipt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("receipts.id"), nullable=False
    )
    subtotal: Mapped[float | None] = mapped_column(Numeric(12, 4))
    total: Mapped[float | None] = mapped_column(Numeric(12, 4))
    calculated_total: Mapped[float | None] = mapped_column(Numeric(12, 4))
    difference: Mapped[float | None] = mapped_column(Numeric(12, 4))
    totals_valid: Mapped[bool | None] = mapped_column(Boolean)

    receipt: Mapped[ReceiptORM] = relationship("ReceiptORM", back_populates="totals")
    taxes: Mapped[list[TaxDetailORM]] = relationship(
        "TaxDetailORM", back_populates="totals", cascade="all, delete-orphan"
    )


class ExtractionJobORM(Base):
    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    receipt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("receipts.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(128))
    overall_confidence: Mapped[float | None] = mapped_column(Float)

    receipt: Mapped[ReceiptORM] = relationship("ReceiptORM", back_populates="jobs")


class ReceiptReviewORM(Base):
    __tablename__ = "receipt_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    receipt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("receipts.id"), nullable=False
    )
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    corrections_json: Mapped[str | None] = mapped_column(Text)

    receipt: Mapped[ReceiptORM] = relationship("ReceiptORM", back_populates="reviews")
