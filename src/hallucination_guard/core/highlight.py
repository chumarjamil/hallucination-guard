"""Text Highlighting — marks hallucinated phrases in original text."""

from __future__ import annotations

import logging
from typing import List

from rich.console import Console
from rich.text import Text

from hallucination_guard.core.scorer import RiskReport
from hallucination_guard.core.verifier import VerificationResult

logger = logging.getLogger(__name__)

FLAG_OPEN = "⚠["
FLAG_CLOSE = "]⚠"


def highlight_plain(original_text: str, report: RiskReport) -> str:
    """Return *original_text* with unsupported claims wrapped in ⚠[…]⚠ markers."""
    flagged_spans = _flagged_spans(report.details)
    if not flagged_spans:
        return original_text

    flagged_spans.sort(key=lambda s: s[0], reverse=True)
    result = original_text
    for start, end in flagged_spans:
        segment = result[start:end]
        result = result[:start] + FLAG_OPEN + segment + FLAG_CLOSE + result[end:]
    return result


def highlight_rich(original_text: str, report: RiskReport) -> Text:
    """Return a Rich Text object with red-highlighted hallucinated spans."""
    rich_text = Text(original_text)
    flagged_spans = _flagged_spans(report.details)
    for start, end in flagged_spans:
        rich_text.stylize("bold red", start, end)
    return rich_text


def print_highlighted(original_text: str, report: RiskReport) -> None:
    """Print highlighted text to terminal via Rich."""
    console = Console()
    rich_text = highlight_rich(original_text, report)
    console.print(rich_text)


def _flagged_spans(results: List[VerificationResult]) -> List[tuple[int, int]]:
    spans: List[tuple[int, int]] = []
    for r in results:
        if not r.is_supported and r.claim.source_span != (0, 0):
            spans.append(r.claim.source_span)
    return spans
