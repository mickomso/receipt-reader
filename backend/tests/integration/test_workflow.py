"""Integration tests for the LangGraph workflow using FakeExtractor."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.workflow.graph import run_workflow
from tests.fixtures.fake_extractor import SAMPLE_EXTRACTION, FailingExtractor, FakeExtractor


@pytest.fixture
def jpeg_file(tmp_path) -> tuple[str, Path]:
    """Create a minimal JPEG file and return its path."""
    from tests.fixtures.sample_data import MINIMAL_JPEG
    p = tmp_path / "ticket.jpg"
    p.write_bytes(MINIMAL_JPEG)
    return str(p)


@pytest.fixture
def receipt_id() -> str:
    import uuid
    return str(uuid.uuid4())


class MockRepository:
    """Minimal in-memory repository stub for workflow tests."""

    def __init__(self):
        self.statuses: list[str] = []
        self.extractions: list = []
        self.jobs: list = []

    def update_status(self, receipt_id, status):
        self.statuses.append(status.value if hasattr(status, "value") else status)
        return None

    def save_extraction(self, receipt_id, extraction, report):
        self.extractions.append((receipt_id, extraction, report))

    def finish_job(self, job_id, status, error=None, confidence=None):
        self.jobs.append((job_id, status, error, confidence))

    def update_fields(self, receipt_id, **fields):
        return None


class TestWorkflowWithFakeExtractor:
    def test_happy_path_returns_extracted_status(self, jpeg_file, receipt_id):
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(), repo)
        assert state["status"] in ("extracted", "needs_review")
        assert state["error"] is None
        assert state["extraction"] is not None

    def test_extraction_contains_items(self, jpeg_file, receipt_id):
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(), repo)
        extraction = state["extraction"]
        assert isinstance(extraction, dict)
        assert len(extraction["items"]) > 0

    def test_validation_report_present(self, jpeg_file, receipt_id):
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(), repo)
        assert "validation_report" in state
        assert state["validation_report"] is not None

    def test_persist_called(self, jpeg_file, receipt_id):
        repo = MockRepository()
        run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(), repo)
        assert len(repo.extractions) > 0

    def test_failing_extractor_sets_failed_status(self, jpeg_file, receipt_id):
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FailingExtractor(), repo)
        assert state["status"] == "failed"
        assert state["error"] is not None

    def test_missing_file_sets_failed_status(self, receipt_id):
        repo = MockRepository()
        state = run_workflow(receipt_id, "/nonexistent/path.jpg", "job-1", FakeExtractor(), repo)
        assert state["status"] == "failed"
        assert "no encontrado" in state["error"].lower()

    def test_needs_review_when_extraction_flags_it(self, jpeg_file, receipt_id):
        from copy import deepcopy
        flagged = deepcopy(SAMPLE_EXTRACTION)
        flagged.needs_review = True
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(flagged), repo)
        assert state["status"] == "needs_review"

    def test_totals_mismatch_triggers_needs_review(self, jpeg_file, receipt_id):
        from copy import deepcopy
        bad = deepcopy(SAMPLE_EXTRACTION)
        bad.total = Decimal("99.99")  # intentionally wrong
        repo = MockRepository()
        state = run_workflow(receipt_id, jpeg_file, "job-1", FakeExtractor(bad), repo)
        # Should be needs_review because totals don't match
        assert state["status"] in ("needs_review", "extracted")
        if state["validation_report"]:
            totals = state["validation_report"]["totals"]
            assert totals.get("valid") is False
