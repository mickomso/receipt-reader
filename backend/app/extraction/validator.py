"""Mathematical validation of extracted receipt data.

No framework imports allowed.  Only stdlib, decimal and the extraction schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from app.extraction.schemas import ReceiptExtractionSchema, ReceiptItemSchema

_CENT = Decimal("0.01")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass
class LineValidationResult:
    position: int
    raw_description: str
    expected: Decimal | None
    declared: Decimal | None
    difference: Decimal | None
    valid: bool | None
    reason: str = ""


@dataclass
class TotalsValidationResult:
    declared_total: Decimal | None
    calculated_total: Decimal | None
    difference: Decimal | None
    valid: bool | None
    reason: str = ""


@dataclass
class ValidationReport:
    lines: list[LineValidationResult] = field(default_factory=list)
    totals: TotalsValidationResult = field(
        default_factory=lambda: TotalsValidationResult(None, None, None, None)
    )
    overall_valid: bool | None = None
    needs_review: bool = False


def validate_line(
    item: ReceiptItemSchema,
    position: int,
    tolerance: Decimal = Decimal("0.01"),
) -> LineValidationResult:
    """Validate quantity * price ≈ total for a single line item."""
    result = LineValidationResult(
        position=position,
        raw_description=item.raw_description,
        expected=None,
        declared=item.total_price,
        difference=None,
        valid=None,
    )

    if item.total_price is None:
        result.reason = "total_price ausente"
        return result

    # Determine expected value
    expected: Decimal | None = None
    if item.unit in ("kg", "g", "l", "ml") and item.price_per_kg is not None and item.quantity is not None:
        # Weight/volume product: quantity * price_per_kg
        qty = item.quantity
        if item.unit == "g":
            qty = qty / Decimal("1000")
        elif item.unit == "ml":
            qty = qty / Decimal("1000")
        expected = _round2(qty * item.price_per_kg)
    elif item.quantity is not None and item.unit_price is not None:
        expected = _round2(item.quantity * item.unit_price)

    if expected is None:
        result.reason = "no se puede calcular el esperado (faltan quantity o unit_price)"
        return result

    # Apply discount if present
    if item.discount is not None:
        expected = _round2(expected - item.discount)

    diff = _round2(item.total_price - expected)
    result.expected = expected
    result.difference = diff
    result.valid = abs(diff) <= tolerance
    if not result.valid:
        result.reason = f"diferencia {diff} EUR supera tolerancia {tolerance} EUR"
    return result


def validate_totals(
    extraction: ReceiptExtractionSchema,
    tolerance: Decimal = Decimal("0.02"),
) -> TotalsValidationResult:
    """Validate sum of line totals ≈ declared total."""
    declared = extraction.total
    item_totals = [i.total_price for i in extraction.items if i.total_price is not None]

    if not item_totals:
        return TotalsValidationResult(
            declared_total=declared,
            calculated_total=None,
            difference=None,
            valid=None,
            reason="sin líneas con total",
        )

    calculated = _round2(sum(item_totals, Decimal("0")))

    # Subtract discounts applied at the basket level (items that are negative totals)
    # (already handled per line above, calculated from item totals directly)

    if declared is None:
        return TotalsValidationResult(
            declared_total=None,
            calculated_total=calculated,
            difference=None,
            valid=None,
            reason="total declarado ausente",
        )

    diff = _round2(declared - calculated)
    valid = abs(diff) <= tolerance
    reason = "" if valid else f"diferencia {diff} EUR supera tolerancia {tolerance} EUR"
    return TotalsValidationResult(
        declared_total=declared,
        calculated_total=calculated,
        difference=diff,
        valid=valid,
        reason=reason,
    )


def run_validation(
    extraction: ReceiptExtractionSchema,
    line_tolerance: Decimal = Decimal("0.01"),
    totals_tolerance: Decimal = Decimal("0.02"),
) -> ValidationReport:
    """Run all validations and return a consolidated report."""
    report = ValidationReport()

    for pos, item in enumerate(extraction.items):
        line_result = validate_line(item, pos, line_tolerance)
        report.lines.append(line_result)

    report.totals = validate_totals(extraction, totals_tolerance)

    # Mark any item needing review
    invalid_lines = [lr for lr in report.lines if lr.valid is False]
    if invalid_lines or extraction.needs_review:
        report.needs_review = True

    # overall_valid: all checkable lines valid AND totals valid
    checkable_lines = [lr for lr in report.lines if lr.valid is not None]
    lines_ok = all(lr.valid for lr in checkable_lines) if checkable_lines else True
    totals_ok = report.totals.valid if report.totals.valid is not None else True
    report.overall_valid = lines_ok and totals_ok

    return report
