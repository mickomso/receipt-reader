"""Tests for state transition edge cases in the service layer."""

from __future__ import annotations


class TestServiceStateTransitions:
    def test_process_only_uploaded(self, client):
        from tests.fixtures.sample_data import MINIMAL_JPEG

        # upload → process → try to process again
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        rid = resp.json()["id"]

        # First process should succeed
        r1 = client.post(f"/api/v1/receipts/{rid}/process")
        assert r1.status_code == 200

        # Second process should fail with 409
        r2 = client.post(f"/api/v1/receipts/{rid}/process")
        assert r2.status_code == 409

    def test_confirm_after_process(self, client):
        from tests.fixtures.sample_data import MINIMAL_JPEG

        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        rid = resp.json()["id"]
        client.post(f"/api/v1/receipts/{rid}/process")

        r = client.post(f"/api/v1/receipts/{rid}/confirm", json={})
        assert r.status_code == 200
        assert r.json()["status"] == "confirmed"

    def test_cannot_confirm_twice(self, client):
        from tests.fixtures.sample_data import MINIMAL_JPEG

        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        rid = resp.json()["id"]
        client.post(f"/api/v1/receipts/{rid}/process")
        client.post(f"/api/v1/receipts/{rid}/confirm", json={})

        r = client.post(f"/api/v1/receipts/{rid}/confirm", json={})
        assert r.status_code == 409

    def test_contract_response_has_required_fields(self, client):
        from tests.fixtures.sample_data import MINIMAL_JPEG

        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        rid = resp.json()["id"]
        r = client.post(f"/api/v1/receipts/{rid}/process")
        data = r.json()

        # Verify contract fields
        assert "id" in data
        assert "status" in data
        assert "items" in data
        assert "totals" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_items_have_required_fields(self, client):
        from tests.fixtures.sample_data import MINIMAL_JPEG

        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        rid = resp.json()["id"]
        r = client.post(f"/api/v1/receipts/{rid}/process")
        items = r.json()["items"]

        assert len(items) > 0
        for item in items:
            assert "raw_description" in item
            assert "needs_review" in item
            assert "position" in item
