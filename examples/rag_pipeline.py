"""
RAG Pipeline Guard — Hallucination Guard
==========================================

Generic pattern for integrating Hallucination Guard into any
Retrieval-Augmented Generation (RAG) pipeline as a verification layer.

Usage:
    python examples/rag_pipeline.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from hallucination_guard import detect


@dataclass
class GuardedResponse:
    """Response wrapper that includes hallucination verification."""

    answer: str
    hallucinated: bool
    risk: float
    confidence: float
    flagged_claims: list
    explanation: str
    safe: bool


class RAGGuard:
    """Wrap any RAG pipeline with automatic hallucination detection.

    Usage::

        def my_rag(query: str) -> str:
            # ... your RAG logic ...
            return answer

        guard = RAGGuard(my_rag, threshold=0.4)
        result = guard.query("What is the capital of France?")

        if result.safe:
            print(result.answer)
        else:
            print(f"⚠ Risk: {result.risk:.0%}")
    """

    def __init__(
        self,
        rag_fn: Callable[[str], str],
        threshold: float = 0.5,
    ) -> None:
        self.rag_fn = rag_fn
        self.threshold = threshold

    def query(self, question: str) -> GuardedResponse:
        """Run the RAG pipeline and verify the output."""
        answer = self.rag_fn(question)
        result = detect(answer)

        return GuardedResponse(
            answer=answer,
            hallucinated=result.hallucinated,
            risk=result.hallucination_risk,
            confidence=result.confidence,
            flagged_claims=result.flagged_claims,
            explanation=result.explanation,
            safe=result.hallucination_risk < self.threshold,
        )


# ---------------------------------------------------------------------------
# Demo with a mock RAG pipeline
# ---------------------------------------------------------------------------

def mock_rag_pipeline(query: str) -> str:
    """Simulated RAG pipeline that sometimes hallucinates."""
    responses = {
        "eiffel tower": (
            "The Eiffel Tower is located in Berlin, Germany. "
            "It was built in 1920 by Leonardo da Vinci."
        ),
        "python": (
            "Python is a high-level programming language created by "
            "Guido van Rossum. It was first released in 1991."
        ),
        "default": (
            "The Great Wall of China was built in 1995 by NASA "
            "as part of the Apollo program."
        ),
    }
    key = query.lower().strip()
    for k, v in responses.items():
        if k in key:
            return v
    return responses["default"]


def main() -> None:
    print("🛡  Hallucination Guard × RAG Pipeline\n")

    guard = RAGGuard(mock_rag_pipeline, threshold=0.4)

    queries = [
        "Tell me about the Eiffel Tower",
        "What is Python?",
        "Tell me about the Great Wall",
    ]

    for query in queries:
        print(f"Q: {query}")
        result = guard.query(query)
        status = "✓ SAFE" if result.safe else "⚠ FLAGGED"
        print(f"A: {result.answer}")
        print(f"   [{status}]  risk={result.risk:.0%}  confidence={result.confidence:.0%}")
        if result.flagged_claims:
            for fc in result.flagged_claims:
                print(f"   → {fc['claim']}")
        print()


if __name__ == "__main__":
    main()
