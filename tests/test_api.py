"""Unit tests for the FastAPI REST API."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from app.main import app, _detector
from app.detector import DetectionResult, HallucinationDetector


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a test client with a mocked detector to avoid heavy model loading."""
    mock_result = DetectionResult(
        hallucination_risk=0.65,
        confidence=0.35,
        total_claims=2,
        supported_claims=1,
        unsupported_claims=1,
        average_similarity=0.42,
        flagged_claims=[
            {
                "claim": "The sky is green.",
                "confidence": 0.15,
                "evidence": "The sky appears blue.",
                "source": "Wikipedia: Sky",
            }
        ],
        highlighted_text="⚠[The sky is green.]⚠ The grass is green.",
    )

    mock_detector = MagicMock(spec=HallucinationDetector)
    mock_detector.detect.return_value = mock_result

    import app.main as main_module
    main_module._detector = mock_detector

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    main_module._detector = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestDetectEndpoint:
    def test_detect_success(self, client):
        resp = client.post("/detect", json={"text": "The sky is green."})
        assert resp.status_code == 200
        data = resp.json()
        assert "hallucination_risk" in data
        assert "flagged_claims" in data
        assert "highlighted_text" in data
        assert isinstance(data["flagged_claims"], list)

    def test_detect_response_structure(self, client):
        resp = client.post("/detect", json={"text": "Test text."})
        data = resp.json()
        assert 0.0 <= data["hallucination_risk"] <= 1.0
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["total_claims"] >= 0

    def test_detect_empty_text_rejected(self, client):
        resp = client.post("/detect", json={"text": ""})
        assert resp.status_code == 422  # validation error

    def test_detect_missing_text_rejected(self, client):
        resp = client.post("/detect", json={})
        assert resp.status_code == 422

    def test_detect_flagged_claims_fields(self, client):
        resp = client.post("/detect", json={"text": "Some claim."})
        data = resp.json()
        for fc in data["flagged_claims"]:
            assert "claim" in fc
            assert "confidence" in fc
            assert "evidence" in fc
