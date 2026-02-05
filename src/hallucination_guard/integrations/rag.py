"""
RAG Pipeline Integration — Hallucination Guard verification hook.

Usage::

    from hallucination_guard.integrations.rag import RAGGuard, rag_verify

    # Decorator style
    @rag_verify(threshold=0.4)
    def my_rag_pipeline(query: str) -> str:
        # ... your RAG logic ...
        return answer

    result = my_rag_pipeline("What is Python?")
    # Raises HallucinationError if risk > threshold

    # Wrapper class style
    guard = RAGGuard(my_rag_fn, threshold=0.4)
    result = guard.query("Tell me about the Eiffel Tower")
    print(result.safe, result.risk)
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GuardedResponse:
    """Result from a guarded RAG query."""

    answer: str
    safe: bool
    risk: float
    confidence: float
    total_claims: int
    unsupported_claims: int
    flagged_claims: list
    explanation: str
    highlighted_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "safe": self.safe,
            "risk": self.risk,
            "confidence": self.confidence,
            "total_claims": self.total_claims,
            "unsupported_claims": self.unsupported_claims,
            "flagged_claims": self.flagged_claims,
            "explanation": self.explanation,
            "highlighted_text": self.highlighted_text,
        }


class RAGGuard:
    """Wrap any RAG pipeline function with hallucination detection.

    Args:
        rag_fn: Function that takes a query string and returns an answer string.
        threshold: Risk threshold (0.0–1.0).
        raise_on_hallucination: Raise exception if threshold exceeded.
        on_hallucination: Optional callback invoked when hallucination detected.
    """

    def __init__(
        self,
        rag_fn: Callable[[str], str],
        threshold: float = 0.5,
        raise_on_hallucination: bool = False,
        on_hallucination: Optional[Callable] = None,
    ) -> None:
        self.rag_fn = rag_fn
        self.threshold = threshold
        self.raise_on_hallucination = raise_on_hallucination
        self.on_hallucination = on_hallucination
        self._guard = None
        self.history: List[GuardedResponse] = []

    def _get_guard(self):
        if self._guard is None:
            from hallucination_guard.core.detector import HallucinationGuard
            self._guard = HallucinationGuard()
        return self._guard

    def query(self, question: str) -> GuardedResponse:
        """Run the RAG pipeline and verify the output."""
        answer = self.rag_fn(question)
        guard = self._get_guard()
        result = guard.detect(answer)

        response = GuardedResponse(
            answer=answer,
            safe=result.hallucination_risk < self.threshold,
            risk=result.hallucination_risk,
            confidence=result.confidence,
            total_claims=result.total_claims,
            unsupported_claims=result.unsupported_claims,
            flagged_claims=result.flagged_claims,
            explanation=result.explanation,
            highlighted_text=result.highlighted_text,
        )
        self.history.append(response)

        if not response.safe:
            logger.warning("RAG hallucination: risk=%.2f query='%s'", response.risk, question[:60])
            if self.on_hallucination:
                self.on_hallucination(response)
            if self.raise_on_hallucination:
                from hallucination_guard.integrations.langchain import HallucinationError
                raise HallucinationError(
                    f"RAG hallucination risk {response.risk:.0%} exceeds {self.threshold:.0%}",
                    result=result,
                )

        return response


def rag_verify(
    threshold: float = 0.5,
    raise_on_hallucination: bool = True,
):
    """Decorator that wraps a RAG function with hallucination verification.

    Usage::

        @rag_verify(threshold=0.4)
        def my_rag(query: str) -> str:
            return "some answer"

        # Automatically verified on each call
        answer = my_rag("What is Python?")
    """
    def decorator(fn: Callable[[str], str]) -> Callable[[str], GuardedResponse]:
        guard = RAGGuard(fn, threshold=threshold, raise_on_hallucination=raise_on_hallucination)

        @functools.wraps(fn)
        def wrapper(query: str) -> GuardedResponse:
            return guard.query(query)

        wrapper.guard = guard  # type: ignore
        return wrapper

    return decorator
