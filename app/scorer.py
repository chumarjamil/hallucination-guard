"""Hallucination Risk Scoring — combines verification signals into a single risk score."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from app.verifier import VerificationResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class RiskReport:
    """Aggregated hallucination risk report."""

    hallucination_risk: float  # 0.0 (safe) → 1.0 (high risk)
    confidence: float          # overall confidence that the text is factual
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    details: List[VerificationResult]


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

class HallucinationScorer:
    """Compute a hallucination risk score from verification results.

    The score is a weighted combination of:
    - **unsupported ratio**: fraction of claims that failed verification
    - **inverse confidence**: average (1 − confidence) across claims
    - **severity bonus**: extra penalty when many claims are unsupported
    """

    WEIGHT_UNSUPPORTED_RATIO: float = 0.50
    WEIGHT_INV_CONFIDENCE: float = 0.35
    WEIGHT_SEVERITY: float = 0.15

    # ---- public API -------------------------------------------------------

    def score(self, results: List[VerificationResult]) -> RiskReport:
        """Return a :class:`RiskReport` for the given verification results."""
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

        # --- component scores ---
        unsupported_ratio = unsupported / total
        inv_confidence = 1.0 - avg_sim

        # severity: non-linear penalty when > 50 % of claims fail
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

        logger.info(
            "Risk score: %.4f  (supported=%d / %d)", risk, supported, total
        )
        return report
