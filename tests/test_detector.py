"""Unit tests for the Orchestration / Detector layer."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.claims import Claim
from app.detector import DetectionResult, HallucinationDetector
from app.verifier import VerificationResult


# ---------------------------------------------------------------------------
# DetectionResult
# ---------------------------------------------------------------------------

class TestDetectionResult:
    def test_fields(self):
        r = DetectionResult(
            hallucination_risk=0.5,
            confidence=0.5,
            total_claims=2,
            supported_claims=1,
            unsupported_claims=1,
            average_similarity=0.4,
            flagged_claims=[],
            highlighted_text="text",
        )
        assert r.hallucination_risk == 0.5
        assert r.highlighted_text == "text"


# ---------------------------------------------------------------------------
# HallucinationDetector (integration-style, mocked network)
# ---------------------------------------------------------------------------

class TestHallucinationDetector:
    @pytest.fixture(scope="class")
    def detector(self):
        return HallucinationDetector()

    def test_detect_returns_result(self, detector: HallucinationDetector):
        with patch.object(detector.verifier.wiki, "search", return_value=None):
            result = detector.detect("Python was created by Guido van Rossum.")
            assert isinstance(result, DetectionResult)
            assert 0.0 <= result.hallucination_risk <= 1.0
            assert isinstance(result.flagged_claims, list)

    def test_detect_empty_text(self, detector: HallucinationDetector):
        result = detector.detect("")
        assert result.total_claims == 0
        assert result.hallucination_risk == 0.0

    def test_detect_highlighted_text_present(self, detector: HallucinationDetector):
        with patch.object(detector.verifier.wiki, "search", return_value=None):
            text = "Albert Einstein invented the telephone."
            result = detector.detect(text)
            assert isinstance(result.highlighted_text, str)
            assert len(result.highlighted_text) >= len(text)

    def test_flagged_claims_structure(self, detector: HallucinationDetector):
        with patch.object(detector.verifier.wiki, "search", return_value=None):
            result = detector.detect("The Moon is made of cheese.")
            for fc in result.flagged_claims:
                assert "claim" in fc
                assert "confidence" in fc
                assert "evidence" in fc
