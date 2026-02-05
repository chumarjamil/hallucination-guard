"""Explanation Generation — produces human-readable explanations for flagged claims."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from hallucination_guard.core.verifier import VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class Explanation:
    """Human-readable explanation for a single claim."""

    claim: str
    hallucinated: bool
    confidence: float
    explanation: str
    evidence: Optional[str] = None
    source: Optional[str] = None
    severity: str = "low"  # low, medium, high


class ExplanationGenerator:
    """Generate structured explanations from verification results."""

    def _severity_label(self, confidence: float, is_supported: bool) -> str:
        if is_supported:
            return "low"
        if confidence < 0.2:
            return "high"
        if confidence < 0.4:
            return "medium"
        return "low"

    def _build_explanation_text(self, vr: VerificationResult) -> str:
        if vr.is_supported:
            return f"This claim appears to be factually supported (similarity: {vr.confidence:.2f})."

        if vr.evidence:
            return (
                f"This claim could not be verified. "
                f"Available evidence suggests otherwise (similarity: {vr.confidence:.2f}). "
                f"Source evidence: {vr.evidence[:200]}"
            )

        return (
            f"This claim could not be verified against any trusted source "
            f"(similarity: {vr.confidence:.2f}). No supporting evidence was found."
        )

    def explain(self, results: List[VerificationResult]) -> List[Explanation]:
        """Generate explanations for each verification result."""
        explanations: List[Explanation] = []

        for vr in results:
            explanation = Explanation(
                claim=vr.claim.text,
                hallucinated=not vr.is_supported,
                confidence=round(vr.confidence, 4),
                explanation=self._build_explanation_text(vr),
                evidence=vr.evidence,
                source=vr.source,
                severity=self._severity_label(vr.confidence, vr.is_supported),
            )
            explanations.append(explanation)

        logger.info(
            "Generated %d explanation(s) — %d flagged",
            len(explanations),
            sum(1 for e in explanations if e.hallucinated),
        )
        return explanations
