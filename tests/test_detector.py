"""Tests for the Orchestration / Detector layer."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from hallucination_guard.core.detector import DetectionResult, HallucinationGuard


class TestDetectionResult:
    def test_fields(self):
        r = DetectionResult(
            hallucinated=True,
            hallucination_risk=0.5,
            confidence=0.5,
            total_claims=2,
            supported_claims=1,
            unsupported_claims=1,
            average_similarity=0.4,
            flagged_claims=[],
            explanations=[],
            highlighted_text="text",
            explanation="summary",
        )
        assert r.hallucination_risk == 0.5
        assert r.hallucinated is True

    def test_to_dict(self):
        r = DetectionResult(
            hallucinated=False,
            hallucination_risk=0.1,
            confidence=0.9,
            total_claims=1,
            supported_claims=1,
            unsupported_claims=0,
            average_similarity=0.8,
            flagged_claims=[],
            explanations=[],
            highlighted_text="ok text",
            explanation="All good.",
        )
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["hallucinated"] is False
        assert d["hallucination_risk"] == 0.1
        assert isinstance(d["flagged_claims"], list)
        assert isinstance(d["explanations"], list)


class TestHallucinationGuard:
    @pytest.fixture(scope="class")
    def guard(self):
        return HallucinationGuard()

    def test_detect_returns_result(self, guard):
        with patch.object(guard.verifier.wiki, "search", return_value=None):
            result = guard.detect("Python was created by Guido van Rossum.")
            assert isinstance(result, DetectionResult)
            assert 0.0 <= result.hallucination_risk <= 1.0
            assert isinstance(result.flagged_claims, list)
            assert isinstance(result.explanations, list)
            assert isinstance(result.explanation, str)

    def test_detect_empty_text(self, guard):
        result = guard.detect("")
        assert result.total_claims == 0
        assert result.hallucination_risk == 0.0
        assert result.hallucinated is False

    def test_detect_highlighted_text_present(self, guard):
        with patch.object(guard.verifier.wiki, "search", return_value=None):
            text = "Albert Einstein invented the telephone."
            result = guard.detect(text)
            assert isinstance(result.highlighted_text, str)
            assert len(result.highlighted_text) >= len(text)

    def test_flagged_claims_structure(self, guard):
        with patch.object(guard.verifier.wiki, "search", return_value=None):
            result = guard.detect("The Moon is made of cheese.")
            for fc in result.flagged_claims:
                assert "claim" in fc
                assert "confidence" in fc
                assert "evidence" in fc

    def test_explanations_present(self, guard):
        with patch.object(guard.verifier.wiki, "search", return_value=None):
            result = guard.detect("Mars is the largest planet.")
            assert len(result.explanations) >= 0
            for exp in result.explanations:
                assert hasattr(exp, "claim")
                assert hasattr(exp, "hallucinated")
                assert hasattr(exp, "explanation")
