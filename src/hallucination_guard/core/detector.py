"""Orchestration layer — the main HallucinationGuard pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from hallucination_guard.core.claims import Claim, ClaimExtractor
from hallucination_guard.core.explainer import Explanation, ExplanationGenerator
from hallucination_guard.core.highlight import highlight_plain
from hallucination_guard.core.scorer import HallucinationScorer, RiskReport
from hallucination_guard.core.verifier import FactVerifier, VerificationResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """Complete detection result returned by the pipeline."""

    hallucinated: bool
    hallucination_risk: float
    confidence: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    flagged_claims: List[dict]
    explanations: List[Explanation]
    highlighted_text: str
    explanation: str  # top-level summary explanation

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-safe)."""
        return {
            "hallucinated": self.hallucinated,
            "hallucination_risk": self.hallucination_risk,
            "confidence": self.confidence,
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "unsupported_claims": self.unsupported_claims,
            "average_similarity": self.average_similarity,
            "flagged_claims": self.flagged_claims,
            "explanations": [
                {
                    "claim": e.claim,
                    "hallucinated": e.hallucinated,
                    "confidence": e.confidence,
                    "explanation": e.explanation,
                    "severity": e.severity,
                    "source": e.source,
                }
                for e in self.explanations
            ],
            "highlighted_text": self.highlighted_text,
            "explanation": self.explanation,
        }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

class HallucinationGuard:
    """Full hallucination-detection pipeline.

    Usage::

        guard = HallucinationGuard()
        result = guard.detect("The Eiffel Tower is in Berlin.")
        print(result.hallucinated)     # True
        print(result.confidence)       # 0.91
        print(result.explanation)      # "…"
    """

    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        transformer_model: str = "all-MiniLM-L6-v2",
        wiki_lang: str = "en",
    ) -> None:
        logger.info("Initialising HallucinationGuard …")
        self.extractor = ClaimExtractor(model_name=spacy_model)
        self.verifier = FactVerifier(
            wiki_lang=wiki_lang,
            transformer_model=transformer_model,
        )
        self.scorer = HallucinationScorer()
        self.explainer = ExplanationGenerator()

    def detect(self, text: str) -> DetectionResult:
        """Run the full detection pipeline on *text*."""
        # 1. Extract claims
        claims: List[Claim] = self.extractor.extract(text)
        logger.info("Pipeline — extracted %d claim(s)", len(claims))

        # 2. Verify
        verification_results: List[VerificationResult] = self.verifier.verify(claims)

        # 3. Score
        report: RiskReport = self.scorer.score(verification_results)

        # 4. Explain
        explanations: List[Explanation] = self.explainer.explain(verification_results)

        # 5. Highlight
        highlighted = highlight_plain(text, report)

        # 6. Build flagged claims
        flagged: List[dict] = []
        for vr in verification_results:
            if not vr.is_supported:
                flagged.append({
                    "claim": vr.claim.text,
                    "confidence": round(vr.confidence, 4),
                    "evidence": vr.evidence or "No supporting evidence found.",
                    "source": vr.source or "N/A",
                })

        # 7. Summary explanation
        hallucinated = report.unsupported_claims > 0
        if hallucinated:
            summary = (
                f"Detected {report.unsupported_claims} unsupported claim(s) "
                f"out of {report.total_claims}. "
                f"Hallucination risk: {report.hallucination_risk:.0%}."
            )
        else:
            summary = (
                f"All {report.total_claims} claim(s) appear factually supported. "
                f"Confidence: {report.confidence:.0%}."
            )

        return DetectionResult(
            hallucinated=hallucinated,
            hallucination_risk=report.hallucination_risk,
            confidence=report.confidence,
            total_claims=report.total_claims,
            supported_claims=report.supported_claims,
            unsupported_claims=report.unsupported_claims,
            average_similarity=report.average_similarity,
            flagged_claims=flagged,
            explanations=explanations,
            highlighted_text=highlighted,
            explanation=summary,
        )
