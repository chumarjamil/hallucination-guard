"""
LangChain Integration — Hallucination Guard callback handler.

Usage::

    from hallucination_guard.integrations.langchain import HallucinationCallback

    callback = HallucinationCallback(threshold=0.5)

    # With LangChain
    llm = ChatOpenAI(callbacks=[callback])
    response = llm.invoke("Tell me about the Eiffel Tower")

    # Check results
    print(callback.last_result)
    print(callback.flagged)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HallucinationCallback:
    """LangChain-compatible callback handler that checks LLM outputs for hallucinations.

    Works with any LangChain ``BaseCallbackHandler`` interface.
    Detects hallucinations in LLM-generated text and optionally raises on failure.

    Args:
        threshold: Risk threshold (0.0–1.0). Outputs above this are flagged.
        raise_on_hallucination: If True, raises ``HallucinationError`` when flagged.
        on_hallucination: Optional callback function called with ``DetectionResult``.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        raise_on_hallucination: bool = False,
        on_hallucination: Optional[Any] = None,
    ) -> None:
        self.threshold = threshold
        self.raise_on_hallucination = raise_on_hallucination
        self.on_hallucination = on_hallucination
        self._guard = None
        self.last_result = None
        self.flagged: bool = False
        self.history: List[Dict[str, Any]] = []

    def _get_guard(self):
        if self._guard is None:
            from hallucination_guard.core.detector import HallucinationGuard
            self._guard = HallucinationGuard()
        return self._guard

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM finishes generating. Checks output for hallucinations."""
        text = self._extract_text(response)
        if not text:
            return
        self._check(text)

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        """Called when chain finishes. Checks output for hallucinations."""
        text = self._extract_chain_text(outputs)
        if not text:
            return
        self._check(text)

    def check(self, text: str) -> Dict[str, Any]:
        """Manually check a text string. Returns result dict."""
        return self._check(text)

    def _check(self, text: str) -> Dict[str, Any]:
        guard = self._get_guard()
        result = guard.detect(text)
        self.last_result = result
        self.flagged = result.hallucination_risk >= self.threshold

        entry = {
            "text": text[:200],
            "risk": result.hallucination_risk,
            "flagged": self.flagged,
            "claims": result.total_claims,
            "unsupported": result.unsupported_claims,
        }
        self.history.append(entry)

        if self.flagged:
            logger.warning(
                "Hallucination detected: risk=%.2f threshold=%.2f",
                result.hallucination_risk,
                self.threshold,
            )
            if self.on_hallucination:
                self.on_hallucination(result)
            if self.raise_on_hallucination:
                raise HallucinationError(
                    f"Hallucination risk {result.hallucination_risk:.0%} "
                    f"exceeds threshold {self.threshold:.0%}",
                    result=result,
                )

        return entry

    @staticmethod
    def _extract_text(response: Any) -> Optional[str]:
        if hasattr(response, "generations"):
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "text"):
                        return gen.text
        if isinstance(response, str):
            return response
        return None

    @staticmethod
    def _extract_chain_text(outputs: Any) -> Optional[str]:
        if isinstance(outputs, dict):
            for key in ("output", "text", "result", "answer"):
                if key in outputs and isinstance(outputs[key], str):
                    return outputs[key]
        if isinstance(outputs, str):
            return outputs
        return None


class HallucinationError(Exception):
    """Raised when hallucination risk exceeds threshold."""

    def __init__(self, message: str, result: Any = None) -> None:
        super().__init__(message)
        self.result = result
