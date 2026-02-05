"""Public SDK functions — convenience wrappers around HallucinationGuard.

Usage::

    from hallucination_guard import detect, score, explain

    result = detect("The Eiffel Tower is in Berlin.")
    risk   = score("Some AI text.")
    info   = explain("Mars is the largest planet.")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from hallucination_guard.core.detector import DetectionResult, HallucinationGuard

logger = logging.getLogger(__name__)

# Lazy singleton — initialised on first call
_guard: HallucinationGuard | None = None


def _get_guard() -> HallucinationGuard:
    global _guard
    if _guard is None:
        _guard = HallucinationGuard()
    return _guard


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(text: str) -> DetectionResult:
    """Run the full hallucination-detection pipeline.

    Args:
        text: AI-generated text to analyse.

    Returns:
        A :class:`DetectionResult` with risk score, flagged claims,
        explanations, and highlighted text.
    """
    return _get_guard().detect(text)


def score(text: str) -> float:
    """Return the hallucination risk score (0.0 – 1.0) for *text*.

    Quick helper when you only need the numeric risk.
    """
    result = _get_guard().detect(text)
    return result.hallucination_risk


def explain(text: str) -> Dict[str, Any]:
    """Return a structured explanation dict for *text*.

    Returns a dict with keys:
        - ``hallucinated`` (bool)
        - ``confidence`` (float)
        - ``explanation`` (str)
        - ``claims`` (list of claim dicts)
    """
    result = _get_guard().detect(text)

    claims: List[Dict[str, Any]] = []
    for exp in result.explanations:
        claims.append({
            "claim": exp.claim,
            "hallucinated": exp.hallucinated,
            "confidence": exp.confidence,
            "explanation": exp.explanation,
            "severity": exp.severity,
            "source": exp.source,
        })

    return {
        "hallucinated": result.hallucinated,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "claims": claims,
    }
