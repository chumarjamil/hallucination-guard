"""
Hallucination Guard — Open-source hallucination detection for AI-generated text.

Usage::

    from hallucination_guard import detect, score, explain

    result = detect("The Eiffel Tower is in Berlin.")
    print(result.hallucinated)       # True
    print(result.confidence)         # 0.91
    print(result.explanation)        # "The Eiffel Tower is in Paris, France …"

    risk = score("Some AI text here.")
    print(risk)                      # 0.72

    info = explain("Mars is the largest planet in the solar system.")
    print(info)                      # Detailed explanation dict
"""

from __future__ import annotations

__version__ = "0.2.0"
__all__ = ["detect", "score", "explain", "HallucinationGuard"]

from hallucination_guard.core.detector import HallucinationGuard
from hallucination_guard.sdk import detect, explain, score
