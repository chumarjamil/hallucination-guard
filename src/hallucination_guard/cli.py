"""
Hallucination Guard CLI — detect hallucinations from the command line.

Usage::

    hallucination-guard check "The Eiffel Tower is in Berlin."
    hallucination-guard file input.txt
    hallucination-guard batch input.json
    hallucination-guard api --port 8000
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hallucination_guard import __version__

app = typer.Typer(
    name="hallucination-guard",
    help="Detect hallucinations in AI-generated text.",
    add_completion=False,
    no_args_is_help=True,
)

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


def _risk_label(risk: float) -> str:
    if risk < 0.3:
        return "LOW"
    if risk < 0.6:
        return "MEDIUM"
    return "HIGH"


def _print_result(text: str, result, *, json_output: bool = False) -> None:
    """Pretty-print a detection result to the terminal."""
    if json_output:
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return

    color = _risk_color(result.hallucination_risk)
    label = _risk_label(result.hallucination_risk)

    # Header panel
    console.print()
    console.print(
        Panel(
            f"[bold {color}]{result.hallucination_risk:.0%} Hallucination Risk  [{label}][/bold {color}]",
            title="[bold]🛡  Hallucination Guard[/bold]",
            subtitle=f"confidence {result.confidence:.0%}",
            border_style=color,
        )
    )

    # Summary
    console.print(f"  Total claims   : {result.total_claims}")
    console.print(f"  Supported      : [green]{result.supported_claims}[/green]")
    console.print(f"  Unsupported    : [red]{result.unsupported_claims}[/red]")
    console.print(f"  Avg similarity : {result.average_similarity:.4f}")
    console.print()

    # Explanation
    console.print(f"  [dim]{result.explanation}[/dim]")
    console.print()

    # Highlighted text
    console.print("[bold underline]Highlighted Text[/bold underline]")
    console.print(f"  {result.highlighted_text}")
    console.print()

    # Flagged claims table
    if result.flagged_claims:
        table = Table(title="Flagged Claims", show_lines=True, border_style="red")
        table.add_column("#", style="dim", width=4)
        table.add_column("Claim", style="bold red", max_width=50)
        table.add_column("Confidence", justify="right", width=12)
        table.add_column("Evidence", max_width=40)
        table.add_column("Source", style="dim", max_width=20)

        for idx, fc in enumerate(result.flagged_claims, 1):
            table.add_row(
                str(idx),
                fc["claim"][:100],
                f"{fc['confidence']:.4f}",
                (fc["evidence"] or "—")[:100],
                fc.get("source", "—")[:30],
            )
        console.print(table)
    else:
        console.print("[green]✓ No flagged claims — text appears factual.[/green]")

    # Per-claim explanations
    if result.explanations:
        console.print()
        console.print("[bold underline]Explanations[/bold underline]")
        for i, exp in enumerate(result.explanations, 1):
            icon = "🔴" if exp.hallucinated else "🟢"
            sev = f" [{exp.severity}]" if exp.hallucinated else ""
            console.print(f"  {icon} [{i}] {exp.claim[:80]}{sev}")
            console.print(f"      [dim]{exp.explanation[:120]}[/dim]")

    console.print()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s | %(name)s | %(message)s",
    )


def _lazy_guard():
    """Import and create HallucinationGuard lazily for fast CLI startup."""
    from hallucination_guard.core.detector import HallucinationGuard
    return HallucinationGuard()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def check(
    text: str = typer.Argument(..., help="Text to check for hallucinations."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
) -> None:
    """Check a text string for hallucinations."""
    _setup_logging(verbose)
    with console.status("[bold green]Analysing …[/bold green]"):
        guard = _lazy_guard()
        result = guard.detect(text)
    _print_result(text, result, json_output=json_output)


@app.command()
def file(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to text file."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
) -> None:
    """Check a text file for hallucinations."""
    _setup_logging(verbose)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        console.print("[red]Error: file is empty.[/red]")
        raise typer.Exit(1)

    with console.status(f"[bold green]Analysing {path.name} …[/bold green]"):
        guard = _lazy_guard()
        result = guard.detect(text)
    _print_result(text, result, json_output=json_output)


@app.command()
def batch(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to JSON file with texts."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
) -> None:
    """Batch-check multiple texts from a JSON file.

    JSON file should be an array of strings or objects with a "text" key.
    """
    _setup_logging(verbose)
    raw = json.loads(path.read_text(encoding="utf-8"))

    texts: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
    else:
        console.print("[red]Error: JSON file must contain an array.[/red]")
        raise typer.Exit(1)

    if not texts:
        console.print("[red]Error: no texts found in JSON file.[/red]")
        raise typer.Exit(1)

    guard = _lazy_guard()
    results = []

    with console.status(f"[bold green]Analysing {len(texts)} text(s) …[/bold green]"):
        for text in texts:
            result = guard.detect(text)
            results.append(result)

    if json_output:
        output = [r.to_dict() for r in results]
        console.print_json(json.dumps(output, indent=2))
    else:
        console.print()
        table = Table(title=f"Batch Results — {len(texts)} texts", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Text", max_width=50)
        table.add_column("Risk", justify="right", width=8)
        table.add_column("Label", width=8)
        table.add_column("Claims", justify="right", width=8)
        table.add_column("Flagged", justify="right", width=8)

        for idx, (text, result) in enumerate(zip(texts, results), 1):
            color = _risk_color(result.hallucination_risk)
            label = _risk_label(result.hallucination_risk)
            table.add_row(
                str(idx),
                text[:80],
                f"[{color}]{result.hallucination_risk:.0%}[/{color}]",
                f"[{color}]{label}[/{color}]",
                str(result.total_claims),
                str(result.unsupported_claims),
            )
        console.print(table)
        console.print()


@app.command("api")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind address."),
    port: int = typer.Option(8000, "--port", "-p", help="Port number."),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging."),
) -> None:
    """Start the REST API server."""
    _setup_logging(verbose)
    import uvicorn

    console.print(
        Panel(
            f"[bold green]Starting API server on {host}:{port}[/bold green]",
            title="[bold]🛡  Hallucination Guard API[/bold]",
        )
    )
    uvicorn.run(
        "hallucination_guard.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if verbose else "info",
    )


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(f"hallucination-guard {__version__}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
