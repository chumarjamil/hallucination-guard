"""Tests for the Explanation Generation engine."""

from __future__ import annotations

import pytest

from hallucination_guard.core.claims import Claim
from hallucination_guard.core.explainer import Explanation, ExplanationGenerator
from hallucination_guard.core.verifier import VerificationResult


def _make_vr(supported: bool, confidence: float, evidence: str | None = None) -> VerificationResult:
    return VerificationResult(
        claim=Claim(text="Test claim about something."),
        is_supported=supported,
        confidence=confidence,
        similarity_score=confidence,
        evidence=evidence,
        source="Wikipedia: Test" if evidence else None,
    )


class TestExplanationGenerator:
    @pytest.fixture
    def generator(self):
        return ExplanationGenerator()

    def test_supported_claim(self, generator):
        results = [_make_vr(True, 0.85, "Some evidence text.")]
        explanations = generator.explain(results)
        assert len(explanations) == 1
        assert explanations[0].hallucinated is False
        assert "supported" in explanations[0].explanation.lower()

    def test_unsupported_claim_with_evidence(self, generator):
        results = [_make_vr(False, 0.2, "Contradicting evidence.")]
        explanations = generator.explain(results)
        assert len(explanations) == 1
        assert explanations[0].hallucinated is True
        assert "verified" in explanations[0].explanation.lower()

    def test_unsupported_claim_no_evidence(self, generator):
        results = [_make_vr(False, 0.1, None)]
        explanations = generator.explain(results)
        assert explanations[0].hallucinated is True
        assert "no supporting evidence" in explanations[0].explanation.lower()

    def test_severity_high(self, generator):
        results = [_make_vr(False, 0.1)]
        explanations = generator.explain(results)
        assert explanations[0].severity == "high"

    def test_severity_medium(self, generator):
        results = [_make_vr(False, 0.3)]
        explanations = generator.explain(results)
        assert explanations[0].severity == "medium"

    def test_severity_low_supported(self, generator):
        results = [_make_vr(True, 0.9)]
        explanations = generator.explain(results)
        assert explanations[0].severity == "low"

    def test_empty_results(self, generator):
        explanations = generator.explain([])
        assert explanations == []

    def test_explanation_fields(self, generator):
        results = [_make_vr(False, 0.15, "Evidence here.")]
        explanations = generator.explain(results)
        exp = explanations[0]
        assert isinstance(exp, Explanation)
        assert isinstance(exp.claim, str)
        assert isinstance(exp.confidence, float)
        assert isinstance(exp.explanation, str)
