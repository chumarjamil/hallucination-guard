"""
Hallucination Guard CLI — world-class developer tooling for hallucination detection.

Usage::

    hallucination-guard check "The Eiffel Tower is in Berlin."
    hallucination-guard check "text" --json
    hallucination-guard file article.txt --pretty --explain
    hallucination-guard batch dataset.json --output results.json
    hallucination-guard benchmark golden.json
    hallucination-guard api --port 8000
"""

from __future__ import annotations

import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.bar import Bar
from rich.columns import Columns
from rich.console import Console
from rich.markup import escape
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from hallucination_guard import __version__

app = typer.Typer(
    name="hallucination-guard",
    help="🛡 Detect hallucinations in AI-generated text.\n\nCLI · SDK · API · Built for developers.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Rendering helpers
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


def _risk_icon(risk: float) -> str:
    if risk < 0.3:
        return "✓"
    if risk < 0.6:
        return "●"
    return "✗"


def _confidence_bar(value: float, width: int = 20) -> Text:
    filled = round(value * width)
    empty = width - filled
    color = "green" if value >= 0.6 else ("yellow" if value >= 0.3 else "red")
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="dim")
    bar.append(f" {value:.0%}", style=f"bold {color}")
    return bar


def _severity_badge(severity: str) -> str:
    colors = {"high": "red", "medium": "yellow", "low": "green"}
    c = colors.get(severity, "dim")
    return f"[{c}]■ {severity.upper()}[/{c}]"


def _setup_logging(debug: bool, quiet: bool) -> None:
    if quiet:
        logging.disable(logging.CRITICAL)
        return
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S",
    )


def _lazy_guard():
    from hallucination_guard.core.detector import HallucinationGuard
    return HallucinationGuard()


def _write_output(data: dict | list, output: Optional[Path]) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if output:
        output.write_text(text, encoding="utf-8")
        console.print(f"[dim]Output written to {output}[/dim]")
    else:
        console.print_json(text)


# ---------------------------------------------------------------------------
# Pretty output renderer
# ---------------------------------------------------------------------------

def _render_result(
    result,
    *,
    show_json: bool = False,
    show_explain: bool = False,
    pretty: bool = True,
    threshold: float = 0.5,
    elapsed: float = 0.0,
    output: Optional[Path] = None,
) -> None:
    if show_json:
        _write_output(result.to_dict(), output)
        return

    risk = result.hallucination_risk
    color = _risk_color(risk)
    label = _risk_label(risk)
    icon = _risk_icon(risk)

    # ── Header panel ──────────────────────────────────────────────────
    header_lines = Text()
    header_lines.append(f"  {icon} ", style=f"bold {color}")
    header_lines.append(f"{risk:.0%} Hallucination Risk", style=f"bold {color}")
    header_lines.append(f"  [{label}]", style=f"bold {color}")

    console.print()
    console.print(
        Panel(
            header_lines,
            title="[bold white]🛡  Hallucination Guard[/bold white]",
            subtitle=f"[dim]{elapsed:.1f}s[/dim]" if elapsed else None,
            border_style=color,
            padding=(0, 2),
        )
    )

    # ── Confidence bar ────────────────────────────────────────────────
    conf_row = Text("  Confidence  ")
    conf_row.append_text(_confidence_bar(result.confidence))
    console.print(conf_row)

    risk_row = Text("  Risk        ")
    risk_row.append_text(_confidence_bar(risk))
    console.print(risk_row)
    console.print()

    # ── Stats ─────────────────────────────────────────────────────────
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column(style="dim", width=16)
    stats_table.add_column()
    stats_table.add_row("Total claims", f"[bold]{result.total_claims}[/bold]")
    stats_table.add_row("Supported", f"[green]{result.supported_claims}[/green]")
    stats_table.add_row("Unsupported", f"[red]{result.unsupported_claims}[/red]")
    stats_table.add_row("Avg similarity", f"{result.average_similarity:.4f}")
    console.print(Padding(stats_table, (0, 2)))
    console.print()

    # ── Summary ───────────────────────────────────────────────────────
    console.print(f"  [dim italic]{result.explanation}[/dim italic]")
    console.print()

    # ── Highlighted text ──────────────────────────────────────────────
    console.print(Rule("Highlighted Text", style="dim"))
    console.print()
    console.print(Padding(Text(result.highlighted_text), (0, 4)))
    console.print()

    # ── Flagged claims table ──────────────────────────────────────────
    if result.flagged_claims:
        console.print(Rule("Flagged Claims", style="red"))
        console.print()

        table = Table(show_lines=True, border_style="red", expand=True)
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Claim", style="bold", ratio=3)
        table.add_column("Confidence", justify="center", width=24)
        table.add_column("Source", style="dim", ratio=1)

        for idx, fc in enumerate(result.flagged_claims, 1):
            conf = fc["confidence"]
            table.add_row(
                str(idx),
                fc["claim"][:120],
                _confidence_bar(conf, width=14),
                fc.get("source", "—") or "—",
            )
        console.print(Padding(table, (0, 2)))
        console.print()
    else:
        console.print()
        console.print("  [green bold]✓[/green bold] [green]All claims verified — text appears factual.[/green]")
        console.print()

    # ── Explanations (if --explain) ───────────────────────────────────
    if show_explain and result.explanations:
        console.print(Rule("Explanations", style="blue"))
        console.print()

        for i, exp in enumerate(result.explanations, 1):
            icon_e = "🔴" if exp.hallucinated else "🟢"
            badge = _severity_badge(exp.severity) if exp.hallucinated else "[green]■ PASS[/green]"

            tree = Tree(f"{icon_e} [bold]Claim {i}[/bold]: {escape(exp.claim[:90])}")
            tree.add(f"Status     : {badge}")
            tree.add(f"Confidence : {_confidence_bar(exp.confidence, width=12)}")
            if exp.hallucinated:
                tree.add(f"[dim]{escape(exp.explanation[:150])}[/dim]")
                if exp.source:
                    tree.add(f"Source: [blue]{escape(exp.source)}[/blue]")

            console.print(Padding(tree, (0, 4)))
        console.print()

    # ── Threshold verdict ─────────────────────────────────────────────
    if risk >= threshold:
        console.print(
            Panel(
                f"[bold red]⚠  FAIL[/bold red]  Risk {risk:.0%} exceeds threshold {threshold:.0%}",
                border_style="red",
                padding=(0, 2),
            )
        )
    else:
        console.print(
            Panel(
                f"[bold green]✓  PASS[/bold green]  Risk {risk:.0%} below threshold {threshold:.0%}",
                border_style="green",
                padding=(0, 2),
            )
        )
    console.print()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def check(
    text: str = typer.Argument(..., help="Text to check for hallucinations."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON."),
    pretty: bool = typer.Option(True, "--pretty/--no-pretty", help="Pretty-print output."),
    explain: bool = typer.Option(False, "--explain", "-e", help="Show per-claim explanations."),
    threshold: float = typer.Option(0.5, "--confidence-threshold", "-t", help="Risk threshold for PASS/FAIL verdict."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output except result."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON output to file."),
) -> None:
    """Check a text string for hallucinations."""
    _setup_logging(debug, quiet)

    t0 = time.perf_counter()
    with console.status("[bold green]Loading models …[/bold green]", spinner="dots"):
        guard = _lazy_guard()
    with console.status("[bold green]Analysing claims …[/bold green]", spinner="dots"):
        result = guard.detect(text)
    elapsed = time.perf_counter() - t0

    _render_result(
        result,
        show_json=json_output or output is not None,
        show_explain=explain,
        pretty=pretty,
        threshold=threshold,
        elapsed=elapsed,
        output=output,
    )


@app.command()
def file(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to text file."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON."),
    pretty: bool = typer.Option(True, "--pretty/--no-pretty", help="Pretty-print output."),
    explain: bool = typer.Option(False, "--explain", "-e", help="Show per-claim explanations."),
    threshold: float = typer.Option(0.5, "--confidence-threshold", "-t", help="Risk threshold."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress extra output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON to file."),
) -> None:
    """Check a text file for hallucinations."""
    _setup_logging(debug, quiet)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        err_console.print("[red bold]Error:[/red bold] file is empty.")
        raise typer.Exit(1)

    if not quiet:
        console.print(f"[dim]Reading {path.name} ({len(text)} chars)[/dim]")

    t0 = time.perf_counter()
    with console.status("[bold green]Loading models …[/bold green]", spinner="dots"):
        guard = _lazy_guard()
    with console.status(f"[bold green]Analysing {path.name} …[/bold green]", spinner="dots"):
        result = guard.detect(text)
    elapsed = time.perf_counter() - t0

    _render_result(
        result,
        show_json=json_output or output is not None,
        show_explain=explain,
        pretty=pretty,
        threshold=threshold,
        elapsed=elapsed,
        output=output,
    )


@app.command()
def batch(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to JSON file with texts."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON."),
    threshold: float = typer.Option(0.5, "--confidence-threshold", "-t", help="Risk threshold."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress extra output."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write JSON results to file."),
) -> None:
    """Batch-check multiple texts from a JSON file.

    Accepts an array of strings or objects with a "text" key.
    """
    _setup_logging(debug, quiet)
    raw = json.loads(path.read_text(encoding="utf-8"))

    texts: list[str] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
    else:
        err_console.print("[red bold]Error:[/red bold] JSON must be an array.")
        raise typer.Exit(1)

    if not texts:
        err_console.print("[red bold]Error:[/red bold] no texts found.")
        raise typer.Exit(1)

    guard = _lazy_guard()
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analysing", total=len(texts))
        for text in texts:
            result = guard.detect(text)
            results.append(result)
            progress.advance(task)

    if json_output or output is not None:
        data = [r.to_dict() for r in results]
        _write_output(data, output)
        return

    # ── Summary table ─────────────────────────────────────────────────
    console.print()
    table = Table(
        title=f"[bold]Batch Results — {len(texts)} texts[/bold]",
        show_lines=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Text", ratio=3)
    table.add_column("Risk", justify="center", width=24)
    table.add_column("Verdict", justify="center", width=8)
    table.add_column("Claims", justify="right", width=7)
    table.add_column("Flagged", justify="right", width=7)

    pass_count = 0
    for idx, (text, result) in enumerate(zip(texts, results), 1):
        risk = result.hallucination_risk
        color = _risk_color(risk)
        label = _risk_label(risk)
        verdict = f"[{color}]{_risk_icon(risk)} {label}[/{color}]"
        if risk < threshold:
            pass_count += 1
        table.add_row(
            str(idx),
            text[:70],
            _confidence_bar(risk, width=14),
            verdict,
            str(result.total_claims),
            str(result.unsupported_claims),
        )
    console.print(table)

    # ── Batch summary ─────────────────────────────────────────────────
    fail_count = len(texts) - pass_count
    console.print()
    console.print(
        f"  [green bold]{pass_count}[/green bold] passed  "
        f"[red bold]{fail_count}[/red bold] failed  "
        f"[dim](threshold {threshold:.0%})[/dim]"
    )
    console.print()


@app.command()
def benchmark(
    path: Path = typer.Argument(..., exists=True, readable=True, help="Path to golden dataset JSON."),
    threshold: float = typer.Option(0.5, "--confidence-threshold", "-t", help="Risk threshold for classification."),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write report to file."),
) -> None:
    """Run benchmark against a golden dataset.

    JSON file: array of objects with "text" (str) and "expected_hallucination" (bool).
    """
    _setup_logging(debug, False)
    raw = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw, list):
        err_console.print("[red bold]Error:[/red bold] dataset must be a JSON array.")
        raise typer.Exit(1)

    cases = []
    for item in raw:
        if isinstance(item, dict) and "text" in item and "expected_hallucination" in item:
            cases.append(item)

    if not cases:
        err_console.print("[red bold]Error:[/red bold] no valid test cases found.")
        raise typer.Exit(1)

    guard = _lazy_guard()

    tp = fp = tn = fn = 0
    details = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Benchmarking", total=len(cases))
        for case in cases:
            t0 = time.perf_counter()
            result = guard.detect(case["text"])
            elapsed = time.perf_counter() - t0
            predicted = result.hallucination_risk >= threshold
            expected = case["expected_hallucination"]

            if predicted and expected:
                tp += 1
            elif predicted and not expected:
                fp += 1
            elif not predicted and expected:
                fn += 1
            else:
                tn += 1

            details.append({
                "text": case["text"][:80],
                "expected": expected,
                "predicted": predicted,
                "risk": round(result.hallucination_risk, 4),
                "correct": predicted == expected,
                "elapsed_s": round(elapsed, 2),
                "category": case.get("category", "—"),
            })
            progress.advance(task)

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    report = {
        "total_cases": total,
        "threshold": threshold,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "details": details,
    }

    if json_output or output is not None:
        _write_output(report, output)
        return

    # ── Pretty benchmark report ───────────────────────────────────────
    console.print()
    console.print(
        Panel(
            "[bold white]Benchmark Report[/bold white]",
            title="[bold]🛡  Hallucination Guard[/bold]",
            border_style="blue",
            padding=(0, 2),
        )
    )

    # Metrics
    metrics_table = Table(show_header=False, box=None, padding=(0, 3))
    metrics_table.add_column(style="bold", width=14)
    metrics_table.add_column(width=30)
    metrics_table.add_row("Accuracy", _confidence_bar(accuracy))
    metrics_table.add_row("Precision", _confidence_bar(precision))
    metrics_table.add_row("Recall", _confidence_bar(recall))
    metrics_table.add_row("F1 Score", _confidence_bar(f1))
    console.print(Padding(metrics_table, (1, 2)))

    # Confusion matrix
    console.print(Rule("Confusion Matrix", style="dim"))
    cm_table = Table(show_lines=True, border_style="dim")
    cm_table.add_column("", width=20, style="bold")
    cm_table.add_column("Predicted: Halluc.", justify="center", width=20)
    cm_table.add_column("Predicted: Factual", justify="center", width=20)
    cm_table.add_row("Actual: Halluc.", f"[green bold]{tp}[/green bold] TP", f"[red]{fn}[/red] FN")
    cm_table.add_row("Actual: Factual", f"[red]{fp}[/red] FP", f"[green bold]{tn}[/green bold] TN")
    console.print(Padding(cm_table, (1, 2)))

    # Detail table
    console.print(Rule("Test Cases", style="dim"))
    dt = Table(show_lines=True, expand=True)
    dt.add_column("#", style="dim", width=3, justify="right")
    dt.add_column("Text", ratio=3)
    dt.add_column("Category", style="dim", width=10)
    dt.add_column("Expected", justify="center", width=10)
    dt.add_column("Risk", justify="center", width=22)
    dt.add_column("Result", justify="center", width=8)

    for i, d in enumerate(details, 1):
        icon = "[green]✓[/green]" if d["correct"] else "[red]✗[/red]"
        exp = "[red]halluc.[/red]" if d["expected"] else "[green]factual[/green]"
        dt.add_row(
            str(i),
            d["text"],
            d["category"],
            exp,
            _confidence_bar(d["risk"], width=12),
            icon,
        )
    console.print(Padding(dt, (0, 2)))

    console.print()
    correct = sum(1 for d in details if d["correct"])
    console.print(
        f"  [bold]{correct}/{total}[/bold] correct  "
        f"[dim]threshold={threshold:.0%}[/dim]"
    )
    console.print()


@app.command("api")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind address."),
    port: int = typer.Option(8000, "--port", "-p", help="Port number."),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    """Start the REST API server."""
    _setup_logging(debug, False)
    import uvicorn

    console.print()
    console.print(
        Panel(
            f"[bold green]  http://{host}:{port}[/bold green]\n"
            f"[dim]  Docs: http://{host}:{port}/docs[/dim]",
            title="[bold white]🛡  Hallucination Guard API[/bold white]",
            border_style="green",
            padding=(0, 2),
        )
    )
    uvicorn.run(
        "hallucination_guard.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
    )


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(f"[bold]hallucination-guard[/bold] {__version__}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    app()


if __name__ == "__main__":
    main()
