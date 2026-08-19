"""Unit tests for monetary validation logic."""

from __future__ import annotations

from decimal import Decimal

from app.extraction.schemas import ReceiptExtractionSchema, ReceiptItemSchema
from app.extraction.validator import (
    run_validation,
    validate_line,
    validate_totals,
)

# ---------------------------------------------------------------------------
# Line validation tests
# ---------------------------------------------------------------------------

class TestValidateLine:
    def test_valid_unit_line(self):
        item = ReceiptItemSchema(
            raw_description="LECHE 1L",
            quantity=Decimal("2"),
            unit="ud",
            unit_price=Decimal("0.89"),
            total_price=Decimal("1.78"),
        )
        result = validate_line(item, 0)
        assert result.valid is True
        assert result.difference == Decimal("0.00")

    def test_invalid_unit_line(self):
        item = ReceiptItemSchema(
            raw_description="YOGUR X4",
            quantity=Decimal("2"),
            unit="ud",
            unit_price=Decimal("1.00"),
            total_price=Decimal("3.00"),  # wrong: should be 2.00
        )
        result = validate_line(item, 0)
        assert result.valid is False
        assert result.difference == Decimal("1.00")

    def test_line_with_discount(self):
        item = ReceiptItemSchema(
            raw_description="YOGUR PROMO",
            quantity=Decimal("1"),
            unit="ud",
            unit_price=Decimal("0.95"),
            discount=Decimal("0.20"),
            total_price=Decimal("0.75"),
        )
        result = validate_line(item, 0)
        assert result.valid is True

    def test_kg_product(self):
        item = ReceiptItemSchema(
            raw_description="MANZANA KG",
            quantity=Decimal("0.856"),
            unit="kg",
            price_per_kg=Decimal("1.99"),
            total_price=Decimal("1.70"),
        )
        result = validate_line(item, 0)
        assert result.valid is True

    def test_gram_product_conversion(self):
        # 500g at 2.00 EUR/kg = 1.00 EUR
        item = ReceiptItemSchema(
            raw_description="PECHUGA 500G",
            quantity=Decimal("500"),
            unit="g",
            price_per_kg=Decimal("2.00"),
            total_price=Decimal("1.00"),
        )
        result = validate_line(item, 0)
        assert result.valid is True

    def test_missing_total_price(self):
        item = ReceiptItemSchema(
            raw_description="ARTÍCULO SIN PRECIO",
            quantity=Decimal("1"),
            unit="ud",
            unit_price=Decimal("1.00"),
            total_price=None,
        )
        result = validate_line(item, 0)
        assert result.valid is None
        assert "ausente" in result.reason

    def test_missing_quantity(self):
        item = ReceiptItemSchema(
            raw_description="ARTÍCULO SIN CANTIDAD",
            total_price=Decimal("1.50"),
        )
        result = validate_line(item, 0)
        assert result.valid is None

    def test_tolerance_boundary(self):
        # Difference of exactly 0.01 — should be valid with default tolerance
        item = ReceiptItemSchema(
            raw_description="ITEM",
            quantity=Decimal("3"),
            unit="ud",
            unit_price=Decimal("0.333"),
            total_price=Decimal("1.00"),  # 3 * 0.333 = 0.999 → diff = 0.001 EUR
        )
        result = validate_line(item, 0, tolerance=Decimal("0.01"))
        assert result.valid is True


# ---------------------------------------------------------------------------
# Totals validation tests
# ---------------------------------------------------------------------------

class TestValidateTotals:
    def _make_extraction(self, items_total: Decimal, declared: Decimal | None) -> ReceiptExtractionSchema:
        return ReceiptExtractionSchema(
            items=[
                ReceiptItemSchema(
                    raw_description="ITEM",
                    total_price=items_total,
                )
            ],
            total=declared,
        )

    def test_totals_match(self):
        ext = self._make_extraction(Decimal("5.58"), Decimal("5.58"))
        result = validate_totals(ext)
        assert result.valid is True
        assert result.difference == Decimal("0.00")

    def test_totals_within_tolerance(self):
        ext = self._make_extraction(Decimal("5.58"), Decimal("5.59"))
        result = validate_totals(ext, tolerance=Decimal("0.02"))
        assert result.valid is True

    def test_totals_outside_tolerance(self):
        ext = self._make_extraction(Decimal("5.58"), Decimal("6.00"))
        result = validate_totals(ext, tolerance=Decimal("0.02"))
        assert result.valid is False

    def test_missing_declared_total(self):
        ext = self._make_extraction(Decimal("5.58"), None)
        result = validate_totals(ext)
        assert result.valid is None
        assert result.calculated_total == Decimal("5.58")

    def test_no_item_totals(self):
        ext = ReceiptExtractionSchema(
            items=[ReceiptItemSchema(raw_description="ITEM SIN PRECIO")],
            total=Decimal("1.00"),
        )
        result = validate_totals(ext)
        assert result.valid is None

    def test_multiple_items_sum(self):
        ext = ReceiptExtractionSchema(
            items=[
                ReceiptItemSchema(raw_description="A", total_price=Decimal("1.78")),
                ReceiptItemSchema(raw_description="B", total_price=Decimal("1.35")),
                ReceiptItemSchema(raw_description="C", total_price=Decimal("1.70")),
                ReceiptItemSchema(raw_description="D", total_price=Decimal("0.75")),
            ],
            total=Decimal("5.58"),
        )
        result = validate_totals(ext, tolerance=Decimal("0.02"))
        assert result.valid is True
        assert result.calculated_total == Decimal("5.58")


# ---------------------------------------------------------------------------
# Full validation report tests
# ---------------------------------------------------------------------------

class TestRunValidation:
    def test_valid_extraction_no_review(self):
        ext = ReceiptExtractionSchema(
            items=[
                ReceiptItemSchema(
                    raw_description="LECHE",
                    quantity=Decimal("2"),
                    unit="ud",
                    unit_price=Decimal("0.89"),
                    total_price=Decimal("1.78"),
                )
            ],
            total=Decimal("1.78"),
        )
        report = run_validation(ext)
        assert report.overall_valid is True
        assert report.needs_review is False

    def test_invalid_lines_trigger_review(self):
        ext = ReceiptExtractionSchema(
            items=[
                ReceiptItemSchema(
                    raw_description="ERROR",
                    quantity=Decimal("1"),
                    unit="ud",
                    unit_price=Decimal("1.00"),
                    total_price=Decimal("2.00"),  # wrong
                )
            ],
            total=Decimal("2.00"),
        )
        report = run_validation(ext)
        assert report.needs_review is True
        assert report.overall_valid is False

    def test_extraction_needs_review_flag_propagates(self):
        ext = ReceiptExtractionSchema(
            items=[
                ReceiptItemSchema(
                    raw_description="ITEM",
                    total_price=Decimal("1.00"),
                )
            ],
            total=Decimal("1.00"),
            needs_review=True,  # LLM flagged it
        )
        report = run_validation(ext)
        assert report.needs_review is True
