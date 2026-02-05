"""Tests for the Hallucination Risk Scoring engine."""

from __future__ import annotations

import pytest

from hallucination_guard.core.claims import Claim
from hallucination_guard.core.scorer import HallucinationScorer, RiskReport
from hallucination_guard.core.verifier import VerificationResult


def _make_result(supported: bool, confidence: float) -> VerificationResult:
    return VerificationResult(
        claim=Claim(text="test"),
        is_supported=supported,
        confidence=confidence,
        similarity_score=confidence,
    )


class TestHallucinationScorer:
    @pytest.fixture
    def scorer(self):
        return HallucinationScorer()

    def test_no_claims_returns_zero_risk(self, scorer):
        report = scorer.score([])
        assert report.hallucination_risk == 0.0
        assert report.confidence == 1.0
        assert report.total_claims == 0

    def test_all_supported_low_risk(self, scorer):
        results = [_make_result(True, 0.9) for _ in range(5)]
        report = scorer.score(results)
        assert report.hallucination_risk < 0.2
        assert report.supported_claims == 5

    def test_all_unsupported_high_risk(self, scorer):
        results = [_make_result(False, 0.1) for _ in range(5)]
        report = scorer.score(results)
        assert report.hallucination_risk > 0.7
        assert report.unsupported_claims == 5

    def test_mixed_results(self, scorer):
        results = [
            _make_result(True, 0.85),
            _make_result(True, 0.75),
            _make_result(False, 0.2),
            _make_result(False, 0.1),
        ]
        report = scorer.score(results)
        assert 0.2 < report.hallucination_risk < 0.9
        assert report.total_claims == 4

    def test_risk_in_valid_range(self, scorer):
        results = [_make_result(False, 0.0)]
        report = scorer.score(results)
        assert 0.0 <= report.hallucination_risk <= 1.0
        assert 0.0 <= report.confidence <= 1.0

    def test_report_has_details(self, scorer):
        results = [_make_result(True, 0.8)]
        report = scorer.score(results)
        assert isinstance(report, RiskReport)
        assert len(report.details) == 1

    def test_average_similarity(self, scorer):
        results = [_make_result(True, 0.6), _make_result(True, 0.8)]
        report = scorer.score(results)
        assert abs(report.average_similarity - 0.7) < 0.01
