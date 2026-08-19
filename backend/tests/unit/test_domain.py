"""Unit tests for domain model state transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.models import DomainReceipt, ReceiptStatus


def _make_receipt(status: ReceiptStatus = ReceiptStatus.UPLOADED) -> DomainReceipt:
    return DomainReceipt(
        id=uuid4(),
        filename="test.jpg",
        file_path="/tmp/test.jpg",
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestReceiptStateTransitions:
    def test_uploaded_to_processing(self):
        r = _make_receipt(ReceiptStatus.UPLOADED)
        r.transition_to(ReceiptStatus.PROCESSING)
        assert r.status == ReceiptStatus.PROCESSING

    def test_processing_to_extracted(self):
        r = _make_receipt(ReceiptStatus.PROCESSING)
        r.transition_to(ReceiptStatus.EXTRACTED)
        assert r.status == ReceiptStatus.EXTRACTED

    def test_processing_to_needs_review(self):
        r = _make_receipt(ReceiptStatus.PROCESSING)
        r.transition_to(ReceiptStatus.NEEDS_REVIEW)
        assert r.status == ReceiptStatus.NEEDS_REVIEW

    def test_processing_to_failed(self):
        r = _make_receipt(ReceiptStatus.PROCESSING)
        r.transition_to(ReceiptStatus.FAILED)
        assert r.status == ReceiptStatus.FAILED

    def test_extracted_to_confirmed(self):
        r = _make_receipt(ReceiptStatus.EXTRACTED)
        r.transition_to(ReceiptStatus.CONFIRMED)
        assert r.status == ReceiptStatus.CONFIRMED

    def test_needs_review_to_confirmed(self):
        r = _make_receipt(ReceiptStatus.NEEDS_REVIEW)
        r.transition_to(ReceiptStatus.CONFIRMED)
        assert r.status == ReceiptStatus.CONFIRMED

    def test_invalid_transition_raises(self):
        r = _make_receipt(ReceiptStatus.UPLOADED)
        with pytest.raises(ValueError, match="Invalid transition"):
            r.transition_to(ReceiptStatus.CONFIRMED)

    def test_confirmed_cannot_transition(self):
        r = _make_receipt(ReceiptStatus.CONFIRMED)
        with pytest.raises(ValueError):
            r.transition_to(ReceiptStatus.UPLOADED)

    def test_can_process_only_when_uploaded(self):
        assert _make_receipt(ReceiptStatus.UPLOADED).can_process() is True
        assert _make_receipt(ReceiptStatus.PROCESSING).can_process() is False
        assert _make_receipt(ReceiptStatus.EXTRACTED).can_process() is False

    def test_can_confirm_when_extracted_or_needs_review(self):
        assert _make_receipt(ReceiptStatus.EXTRACTED).can_confirm() is True
        assert _make_receipt(ReceiptStatus.NEEDS_REVIEW).can_confirm() is True
        assert _make_receipt(ReceiptStatus.UPLOADED).can_confirm() is False
        assert _make_receipt(ReceiptStatus.CONFIRMED).can_confirm() is False
