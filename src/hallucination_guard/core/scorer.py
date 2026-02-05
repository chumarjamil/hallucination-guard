"""Hallucination Risk Scoring — combines verification signals into a single risk score."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from hallucination_guard.core.verifier import VerificationResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RiskReport:
    """Aggregated hallucination risk report."""

    hallucination_risk: float
    confidence: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    details: List[VerificationResult]


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------

class HallucinationScorer:
    """Compute hallucination risk score from verification results.

    Score = weighted combination of:
    - unsupported ratio (50%)
    - inverse confidence (35%)
    - severity penalty (15%)
    """

    WEIGHT_UNSUPPORTED_RATIO: float = 0.50
    WEIGHT_INV_CONFIDENCE: float = 0.35
    WEIGHT_SEVERITY: float = 0.15

    def score(self, results: List[VerificationResult]) -> RiskReport:
        total = len(results)

        if total == 0:
            return RiskReport(
                hallucination_risk=0.0,
                confidence=1.0,
                total_claims=0,
                supported_claims=0,
                unsupported_claims=0,
                average_similarity=0.0,
                details=[],
            )

        supported = sum(1 for r in results if r.is_supported)
        unsupported = total - supported
        avg_sim = sum(r.similarity_score for r in results) / total

        unsupported_ratio = unsupported / total
        inv_confidence = 1.0 - avg_sim

        if unsupported_ratio > 0.5:
            severity = min(1.0, unsupported_ratio * 1.5)
        else:
            severity = unsupported_ratio * 0.5

        risk = (
            self.WEIGHT_UNSUPPORTED_RATIO * unsupported_ratio
            + self.WEIGHT_INV_CONFIDENCE * inv_confidence
            + self.WEIGHT_SEVERITY * severity
        )
        risk = round(max(0.0, min(1.0, risk)), 4)
        confidence = round(1.0 - risk, 4)

        report = RiskReport(
            hallucination_risk=risk,
            confidence=confidence,
            total_claims=total,
            supported_claims=supported,
            unsupported_claims=unsupported,
            average_similarity=round(avg_sim, 4),
            details=results,
        )

        logger.info("Risk score: %.4f (supported=%d/%d)", risk, supported, total)
        return report
