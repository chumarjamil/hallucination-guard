"""Orchestration layer — ties together claim extraction, verification, scoring, and highlighting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from app.claims import Claim, ClaimExtractor
from app.highlight import highlight_plain
from app.scorer import HallucinationScorer, RiskReport
from app.verifier import FactVerifier, VerificationResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# High-level response model (used by API + SDK)
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """Complete detection result returned to the caller."""

    hallucination_risk: float
    confidence: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    flagged_claims: List[dict]
    highlighted_text: str


# ---------------------------------------------------------------------------
# Main detector (Python SDK entry-point)
# ---------------------------------------------------------------------------

class HallucinationDetector:
    """Orchestrates the full hallucination-detection pipeline.

    Usage::

        detector = HallucinationDetector()
        result = detector.detect("Some AI-generated text …")
        print(result.hallucination_risk)
    """

    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        transformer_model: str = "all-MiniLM-L6-v2",
        wiki_lang: str = "en",
    ) -> None:
        logger.info("Initialising HallucinationDetector …")
        self.extractor = ClaimExtractor(model_name=spacy_model)
        self.verifier = FactVerifier(
            wiki_lang=wiki_lang,
            transformer_model=transformer_model,
        )
        self.scorer = HallucinationScorer()

    # ---- public API -------------------------------------------------------

    def detect(self, text: str) -> DetectionResult:
        """Run the full detection pipeline on *text* and return a :class:`DetectionResult`."""
        # 1. Extract claims
        claims: List[Claim] = self.extractor.extract(text)
        logger.info("Pipeline — extracted %d claim(s)", len(claims))

        # 2. Verify claims
        verification_results: List[VerificationResult] = self.verifier.verify(claims)

        # 3. Score risk
        report: RiskReport = self.scorer.score(verification_results)

        # 4. Highlight
        highlighted = highlight_plain(text, report)

        # 5. Build flagged-claims list
        flagged: List[dict] = []
        for vr in verification_results:
            if not vr.is_supported:
                flagged.append(
                    {
                        "claim": vr.claim.text,
                        "confidence": round(vr.confidence, 4),
                        "evidence": vr.evidence or "No supporting evidence found.",
                        "source": vr.source or "N/A",
                    }
                )

        return DetectionResult(
            hallucination_risk=report.hallucination_risk,
            confidence=report.confidence,
            total_claims=report.total_claims,
            supported_claims=report.supported_claims,
            unsupported_claims=report.unsupported_claims,
            average_similarity=report.average_similarity,
            flagged_claims=flagged,
            highlighted_text=highlighted,
        )
