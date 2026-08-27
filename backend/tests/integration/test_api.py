"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.fixtures.sample_data import MINIMAL_JPEG, MINIMAL_PNG


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestUploadEndpoint:
    def test_upload_valid_jpeg(self, client: TestClient):
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "uploaded"
        assert "id" in data
        assert data["filename"] == "ticket.jpg"

    def test_upload_valid_png(self, client: TestClient):
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.png", MINIMAL_PNG, "image/png")},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "uploaded"

    def test_upload_invalid_mime_rejected(self, client: TestClient):
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert resp.status_code == 400

    def test_upload_too_large_rejected(self, client: TestClient):
        big_content = MINIMAL_JPEG + b"\x00" * (11 * 1024 * 1024)
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("big.jpg", big_content, "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "límite" in resp.json()["detail"].lower() or "mb" in resp.json()["detail"].lower()

    def test_upload_content_mismatch_rejected(self, client: TestClient):
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("fake.jpg", b"not a real jpeg at all", "image/jpeg")},
        )
        assert resp.status_code == 400


class TestProcessEndpoint:
    def _upload(self, client: TestClient) -> str:
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_process_returns_extracted_data(self, client: TestClient):
        receipt_id = self._upload(client)
        resp = client.post(f"/api/v1/receipts/{receipt_id}/process")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("extracted", "needs_review")
        assert len(data["items"]) > 0

    def test_process_nonexistent_receipt(self, client: TestClient):
        resp = client.post("/api/v1/receipts/nonexistent-id/process")
        assert resp.status_code == 404

    def test_process_already_processed_returns_409(self, client: TestClient):
        receipt_id = self._upload(client)
        client.post(f"/api/v1/receipts/{receipt_id}/process")
        resp = client.post(f"/api/v1/receipts/{receipt_id}/process")
        assert resp.status_code == 409


class TestListAndDetailEndpoints:
    def test_list_receipts_empty(self, client: TestClient):
        resp = client.get("/api/v1/receipts")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_receipts_after_upload(self, client: TestClient):
        client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        resp = client.get("/api/v1/receipts")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) >= 1

    def test_delete_receipt(self, client: TestClient):
        upload_resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        receipt_id = upload_resp.json()["id"]

        resp = client.delete(f"/api/v1/receipts/{receipt_id}")

        assert resp.status_code == 204
        assert client.get(f"/api/v1/receipts/{receipt_id}").status_code == 404

    def test_delete_nonexistent_receipt(self, client: TestClient):
        resp = client.delete("/api/v1/receipts/does-not-exist")
        assert resp.status_code == 404

    def test_get_receipt_detail(self, client: TestClient):
        upload_resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        receipt_id = upload_resp.json()["id"]
        resp = client.get(f"/api/v1/receipts/{receipt_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == receipt_id

    def test_get_nonexistent_receipt(self, client: TestClient):
        resp = client.get("/api/v1/receipts/does-not-exist")
        assert resp.status_code == 404


class TestPatchAndConfirmEndpoints:
    def _upload_and_process(self, client: TestClient) -> str:
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        receipt_id = resp.json()["id"]
        client.post(f"/api/v1/receipts/{receipt_id}/process")
        return receipt_id

    def test_patch_commerce(self, client: TestClient):
        receipt_id = self._upload_and_process(client)
        resp = client.patch(
            f"/api/v1/receipts/{receipt_id}",
            json={"commerce": "Mercadona"},
        )
        assert resp.status_code == 200
        assert resp.json()["commerce"] == "Mercadona"

    def test_confirm_extracted_receipt(self, client: TestClient):
        receipt_id = self._upload_and_process(client)
        resp = client.post(
            f"/api/v1/receipts/{receipt_id}/confirm",
            json={"corrections": None},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_confirm_uploaded_receipt_returns_409(self, client: TestClient):
        resp = client.post(
            "/api/v1/receipts",
            files={"file": ("ticket.jpg", MINIMAL_JPEG, "image/jpeg")},
        )
        receipt_id = resp.json()["id"]
        resp = client.post(
            f"/api/v1/receipts/{receipt_id}/confirm",
            json={"corrections": None},
        )
        assert resp.status_code == 409
