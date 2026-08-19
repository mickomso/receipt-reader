"""Fake extractor for use in tests — never calls a real LLM."""

from __future__ import annotations

from decimal import Decimal

from app.extraction.schemas import (
    ReceiptExtractionSchema,
    ReceiptItemSchema,
    TaxDetailSchema,
)
from app.workflow.base_extractor import BaseExtractor

SAMPLE_EXTRACTION = ReceiptExtractionSchema(
    commerce="Supermercado Demo S.A.",
    date="2024-03-15",
    time="10:30",
    currency="EUR",
    ticket_number="0001234",
    items=[
        ReceiptItemSchema(
            raw_description="LECHE ENTERA 1L",
            normalized_description="Leche entera 1 litro",
            quantity=Decimal("2"),
            unit="ud",
            unit_price=Decimal("0.89"),
            discount=None,
            total_price=Decimal("1.78"),
            confidence=0.98,
            needs_review=False,
        ),
        ReceiptItemSchema(
            raw_description="PAN MOLDE INT 500G",
            normalized_description="Pan de molde integral 500g",
            quantity=Decimal("1"),
            unit="ud",
            unit_price=Decimal("1.35"),
            discount=None,
            total_price=Decimal("1.35"),
            confidence=0.97,
            needs_review=False,
        ),
        ReceiptItemSchema(
            raw_description="MANZANA GOLDEN KG",
            normalized_description="Manzana golden",
            quantity=Decimal("0.856"),
            unit="kg",
            price_per_kg=Decimal("1.99"),
            unit_price=None,
            discount=None,
            total_price=Decimal("1.70"),
            confidence=0.95,
            needs_review=False,
        ),
        ReceiptItemSchema(
            raw_description="YOGUR NATURAL X4",
            normalized_description="Yogur natural pack 4 unidades",
            quantity=Decimal("1"),
            unit="ud",
            unit_price=Decimal("0.95"),
            discount=Decimal("0.20"),
            total_price=Decimal("0.75"),
            confidence=0.96,
            needs_review=False,
        ),
    ],
    subtotal=Decimal("5.58"),
    taxes=[
        TaxDetailSchema(
            name="IVA 4%",
            rate=Decimal("0.04"),
            base=Decimal("2.70"),
            amount=Decimal("0.11"),
        ),
        TaxDetailSchema(
            name="IVA 10%",
            rate=Decimal("0.10"),
            base=Decimal("2.88"),
            amount=Decimal("0.29"),
        ),
    ],
    total=Decimal("5.58"),
    payment_method="TARJETA",
    overall_confidence=0.97,
    needs_review=False,
)


class FakeExtractor(BaseExtractor):
    """Returns a fixed extraction result without calling any LLM."""

    def __init__(self, result: ReceiptExtractionSchema = SAMPLE_EXTRACTION) -> None:
        self._result = result

    def extract(self, image_bytes: bytes, mime_type: str) -> ReceiptExtractionSchema:
        return self._result


class FailingExtractor(BaseExtractor):
    """Always raises an exception — for testing error handling."""

    def extract(self, image_bytes: bytes, mime_type: str) -> ReceiptExtractionSchema:
        raise RuntimeError("LLM temporalmente no disponible")
