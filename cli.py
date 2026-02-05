"""CLI interface for Hallucination Guard."""

from __future__ import annotations

import logging
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.detector import HallucinationDetector
from app.highlight import highlight_rich
from app.scorer import RiskReport

console = Console()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _risk_color(risk: float) -> str:
    if risk < 0.3:
        return "green"
    if risk < 0.6:
        return "yellow"
    return "red"


def _print_report(text: str, result, report: RiskReport) -> None:
    """Pretty-print the detection report to the terminal."""
    color = _risk_color(result.hallucination_risk)

    # --- header ---
    console.print()
    console.print(
        Panel(
            f"[bold {color}]Hallucination Risk: {result.hallucination_risk:.2%}[/bold {color}]",
            title="[bold]Hallucination Guard[/bold]",
            subtitle=f"confidence {result.confidence:.2%}",
            border_style=color,
        )
    )

    # --- summary ---
    console.print(f"  Total claims   : {result.total_claims}")
    console.print(f"  Supported      : [green]{result.supported_claims}[/green]")
    console.print(f"  Unsupported    : [red]{result.unsupported_claims}[/red]")
    console.print(f"  Avg similarity : {result.average_similarity:.4f}")
    console.print()

    # --- highlighted text ---
    console.print("[bold underline]Highlighted Text[/bold underline]")
    rich_text = highlight_rich(text, report)
    console.print(rich_text)
    console.print()

    # --- flagged claims table ---
    if result.flagged_claims:
        table = Table(title="Flagged Claims", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Claim", style="bold red", max_width=60)
        table.add_column("Confidence", justify="right", width=12)
        table.add_column("Evidence", max_width=50)

        for idx, fc in enumerate(result.flagged_claims, 1):
            table.add_row(
                str(idx),
                fc["claim"][:120],
                f"{fc['confidence']:.4f}",
                (fc["evidence"] or "—")[:120],
            )

        console.print(table)
    else:
        console.print("[green]No flagged claims — text looks factual.[/green]")

    console.print()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

@click.command("hallucination-check")
@click.argument("text", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Read text from a file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def main(text: str | None, file: str | None, verbose: bool) -> None:
    """Detect hallucinations in AI-generated text."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(name)s | %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    # Resolve input text
    if file:
        with open(file, "r", encoding="utf-8") as fh:
            text = fh.read()
    elif text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            console.print("[red]Error: provide text as an argument, via --file, or pipe via stdin.[/red]")
            raise SystemExit(1)

    if not text or not text.strip():
        console.print("[red]Error: empty input.[/red]")
        raise SystemExit(1)

    # Run detection
    with console.status("[bold green]Analysing text …[/bold green]"):
        detector = HallucinationDetector()
        result = detector.detect(text)

    # Build a RiskReport for the highlighter
    report = RiskReport(
        hallucination_risk=result.hallucination_risk,
        confidence=result.confidence,
        total_claims=result.total_claims,
        supported_claims=result.supported_claims,
        unsupported_claims=result.unsupported_claims,
        average_similarity=result.average_similarity,
        details=detector.scorer.score(
            detector.verifier.verify(detector.extractor.extract(text))
        ).details,
    )

    _print_report(text, result, report)


if __name__ == "__main__":
    main()
