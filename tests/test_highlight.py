"""Tests for the Text Highlighting System."""

from __future__ import annotations

import pytest

from hallucination_guard.core.claims import Claim
from hallucination_guard.core.highlight import highlight_plain, highlight_rich, _flagged_spans
from hallucination_guard.core.scorer import RiskReport
from hallucination_guard.core.verifier import VerificationResult


def _make_report(results: list[VerificationResult]) -> RiskReport:
    return RiskReport(
        hallucination_risk=0.5,
        confidence=0.5,
        total_claims=len(results),
        supported_claims=sum(1 for r in results if r.is_supported),
        unsupported_claims=sum(1 for r in results if not r.is_supported),
        average_similarity=0.5,
        details=results,
    )


class TestFlaggedSpans:
    def test_unsupported_claims_returned(self):
        vr = VerificationResult(
            claim=Claim(text="bad claim", source_span=(10, 20)),
            is_supported=False,
        )
        spans = _flagged_spans([vr])
        assert spans == [(10, 20)]

    def test_supported_claims_excluded(self):
        vr = VerificationResult(
            claim=Claim(text="good claim", source_span=(5, 15)),
            is_supported=True,
        )
        spans = _flagged_spans([vr])
        assert spans == []

    def test_zero_span_excluded(self):
        vr = VerificationResult(
            claim=Claim(text="no span", source_span=(0, 0)),
            is_supported=False,
        )
        spans = _flagged_spans([vr])
        assert spans == []


class TestHighlightPlain:
    def test_no_flagged_returns_original(self):
        text = "Everything is fine."
        report = _make_report([])
        assert highlight_plain(text, report) == text

    def test_flagged_claim_wrapped(self):
        text = "The sky is green today."
        vr = VerificationResult(
            claim=Claim(text="The sky is green today.", source_span=(0, 23)),
            is_supported=False,
        )
        report = _make_report([vr])
        result = highlight_plain(text, report)
        assert "⚠[" in result
        assert "]⚠" in result

    def test_multiple_flagged_claims(self):
        text = "Claim A. Claim B. Claim C."
        vr1 = VerificationResult(
            claim=Claim(text="Claim A.", source_span=(0, 8)),
            is_supported=False,
        )
        vr2 = VerificationResult(
            claim=Claim(text="Claim C.", source_span=(18, 26)),
            is_supported=False,
        )
        report = _make_report([vr1, vr2])
        result = highlight_plain(text, report)
        assert result.count("⚠[") == 2


class TestHighlightRich:
    def test_returns_rich_text(self):
        from rich.text import Text
        text = "Some text here."
        report = _make_report([])
        result = highlight_rich(text, report)
        assert isinstance(result, Text)
