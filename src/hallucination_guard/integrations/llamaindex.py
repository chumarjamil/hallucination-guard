"""
LlamaIndex Integration — Hallucination Guard plugin.

Usage::

    from hallucination_guard.integrations.llamaindex import HallucinationGuardPlugin

    plugin = HallucinationGuardPlugin(threshold=0.5)

    # Verify any response
    result = plugin.verify("AI-generated response text")

    if result["safe"]:
        print("Response is factual")
    else:
        print(f"Flagged: {result['risk']:.0%} risk")

    # Use as a post-processor for query engines
    response = query_engine.query("What is Python?")
    verified = plugin.verify_response(response)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HallucinationGuardPlugin:
    """LlamaIndex-compatible plugin for hallucination detection.

    Can be used as a standalone verifier or integrated into
    LlamaIndex query pipelines as a post-processing step.

    Args:
        threshold: Risk threshold (0.0–1.0).
        raise_on_hallucination: Raise exception if threshold exceeded.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        raise_on_hallucination: bool = False,
    ) -> None:
        self.threshold = threshold
        self.raise_on_hallucination = raise_on_hallucination
        self._guard = None
        self.history: List[Dict[str, Any]] = []

    def _get_guard(self):
        if self._guard is None:
            from hallucination_guard.core.detector import HallucinationGuard
            self._guard = HallucinationGuard()
        return self._guard

    def verify(self, text: str) -> Dict[str, Any]:
        """Verify a text string for hallucinations.

        Returns:
            Dict with keys: safe, risk, confidence, flagged_claims, explanation.
        """
        guard = self._get_guard()
        result = guard.detect(text)

        entry = {
            "safe": result.hallucination_risk < self.threshold,
            "risk": result.hallucination_risk,
            "confidence": result.confidence,
            "total_claims": result.total_claims,
            "unsupported_claims": result.unsupported_claims,
            "flagged_claims": result.flagged_claims,
            "explanation": result.explanation,
            "highlighted_text": result.highlighted_text,
        }
        self.history.append(entry)

        if not entry["safe"]:
            logger.warning(
                "Hallucination detected: risk=%.2f threshold=%.2f",
                result.hallucination_risk,
                self.threshold,
            )
            if self.raise_on_hallucination:
                from hallucination_guard.integrations.langchain import HallucinationError
                raise HallucinationError(
                    f"Hallucination risk {result.hallucination_risk:.0%} "
                    f"exceeds threshold {self.threshold:.0%}",
                    result=result,
                )

        return entry

    def verify_response(self, response: Any) -> Dict[str, Any]:
        """Verify a LlamaIndex Response object."""
        text = str(response) if not isinstance(response, str) else response
        return self.verify(text)

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics from all verifications."""
        if not self.history:
            return {"total": 0, "flagged": 0, "avg_risk": 0.0}

        flagged = sum(1 for h in self.history if not h["safe"])
        avg_risk = sum(h["risk"] for h in self.history) / len(self.history)
        return {
            "total": len(self.history),
            "flagged": flagged,
            "passed": len(self.history) - flagged,
            "avg_risk": round(avg_risk, 4),
            "flag_rate": round(flagged / len(self.history), 4),
        }
