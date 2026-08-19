"""FastAPI request/response schemas (API contract).

These are the public API types.  They may reference domain models
for conversion but must not leak ORM types to the outside.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class TaxDetailOut(BaseModel):
    name: str | None = None
    rate: Decimal | None = None
    base: Decimal | None = None
    amount: Decimal | None = None

    model_config = {"from_attributes": True}


class ReceiptItemOut(BaseModel):
    id: str
    position: int
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

    model_config = {"from_attributes": True}


class ReceiptTotalsOut(BaseModel):
    subtotal: Decimal | None = None
    taxes: list[TaxDetailOut] = []
    total: Decimal | None = None
    calculated_total: Decimal | None = None
    difference: Decimal | None = None
    totals_valid: bool | None = None

    model_config = {"from_attributes": True}


class ReceiptOut(BaseModel):
    id: str
    filename: str
    status: str
    commerce: str | None = None
    date: str | None = None
    time: str | None = None
    currency: str = "EUR"
    ticket_number: str | None = None
    payment_method: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReceiptDetailOut(ReceiptOut):
    items: list[ReceiptItemOut] = []
    totals: ReceiptTotalsOut | None = None


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class ReceiptItemPatch(BaseModel):
    raw_description: str | None = None
    normalized_description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    price_per_kg: Decimal | None = None
    discount: Decimal | None = None
    total_price: Decimal | None = None


class ReceiptPatch(BaseModel):
    commerce: str | None = None
    date: str | None = None
    time: str | None = None
    currency: str | None = None
    ticket_number: str | None = None
    payment_method: str | None = None
    items: list[ReceiptItemPatch] | None = None


class ConfirmRequest(BaseModel):
    corrections: dict | None = Field(
        None, description="Snapshot JSON de las correcciones realizadas antes de confirmar"
    )


# ---------------------------------------------------------------------------
# List response with pagination
# ---------------------------------------------------------------------------

class ReceiptListOut(BaseModel):
    items: list[ReceiptOut]
    total: int
    skip: int
    limit: int
