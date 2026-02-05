"""Tests for the FastAPI REST API."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from hallucination_guard.core.detector import DetectionResult, HallucinationGuard
from hallucination_guard.core.explainer import Explanation
from hallucination_guard.api.server import app


@pytest.fixture(scope="module")
def client():
    mock_result = DetectionResult(
        hallucinated=True,
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
        explanations=[
            Explanation(
                claim="The sky is green.",
                hallucinated=True,
                confidence=0.15,
                explanation="This claim could not be verified.",
                evidence="The sky appears blue.",
                source="Wikipedia: Sky",
                severity="high",
            )
        ],
        highlighted_text="⚠[The sky is green.]⚠ The grass is green.",
        explanation="Detected 1 unsupported claim(s) out of 2.",
    )

    mock_guard = MagicMock(spec=HallucinationGuard)
    mock_guard.detect.return_value = mock_result

    import hallucination_guard.api.server as server_module
    server_module._guard = mock_guard

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    server_module._guard = None


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
        assert "hallucinated" in data
        assert "hallucination_risk" in data
        assert "flagged_claims" in data
        assert "explanations" in data
        assert "highlighted_text" in data
        assert "explanation" in data

    def test_detect_response_structure(self, client):
        resp = client.post("/detect", json={"text": "Test text."})
        data = resp.json()
        assert 0.0 <= data["hallucination_risk"] <= 1.0
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["hallucinated"], bool)

    def test_detect_empty_text_rejected(self, client):
        resp = client.post("/detect", json={"text": ""})
        assert resp.status_code == 422

    def test_detect_missing_text_rejected(self, client):
        resp = client.post("/detect", json={})
        assert resp.status_code == 422

    def test_detect_explanations_present(self, client):
        resp = client.post("/detect", json={"text": "Some claim."})
        data = resp.json()
        assert isinstance(data["explanations"], list)
        for exp in data["explanations"]:
            assert "claim" in exp
            assert "hallucinated" in exp
            assert "explanation" in exp
            assert "severity" in exp
