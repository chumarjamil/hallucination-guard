"""
API Usage Examples — Hallucination Guard
=========================================

Shows different ways to interact with the REST API:
  1. Health check
  2. Single text detection
  3. Batch analysis of multiple texts

Prerequisites:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

Run:
    python examples/api_usage.py
"""

from __future__ import annotations

import json
import sys

import httpx

BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

def example_health_check() -> None:
    """Check if the server is up and running."""
    print("--- Health Check ---")
    resp = httpx.get(f"{BASE_URL}/health", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Body:   {resp.json()}")
    print()


# ---------------------------------------------------------------------------
# 2. Single detection
# ---------------------------------------------------------------------------

def example_single_detection() -> None:
    """Analyse a single piece of AI-generated text."""
    print("--- Single Detection ---")

    text = "The Eiffel Tower is located in Berlin and was built in 1920."

    resp = httpx.post(
        f"{BASE_URL}/detect",
        json={"text": text},
        timeout=120,
    )
    result = resp.json()

    print(f"Input:              {text}")
    print(f"Hallucination risk: {result['hallucination_risk']}")
    print(f"Confidence:         {result['confidence']}")
    print(f"Flagged claims:     {len(result['flagged_claims'])}")
    print(f"Highlighted:        {result['highlighted_text']}")
    print()


# ---------------------------------------------------------------------------
# 3. Batch analysis
# ---------------------------------------------------------------------------

def example_batch_analysis() -> None:
    """Analyse multiple texts and rank by risk."""
    print("--- Batch Analysis ---")

    texts = [
        "Python was created by Guido van Rossum in 1991.",
        "The Great Wall of China was built by NASA in 1995.",
        "Albert Einstein developed the theory of relativity.",
        "The Amazon River flows through the Sahara Desert.",
        "Microsoft was founded by Steve Jobs in Cupertino.",
    ]

    results = []
    for text in texts:
        resp = httpx.post(
            f"{BASE_URL}/detect",
            json={"text": text},
            timeout=120,
        )
        data = resp.json()
        results.append({"text": text, **data})

    # Sort by risk descending
    results.sort(key=lambda r: r["hallucination_risk"], reverse=True)

    print(f"{'Risk':>6}  {'Claims':>6}  Text")
    print("-" * 64)
    for r in results:
        risk_pct = f"{r['hallucination_risk']:.0%}"
        claims = f"{r['unsupported_claims']}/{r['total_claims']}"
        print(f"{risk_pct:>6}  {claims:>6}  {r['text'][:50]}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n🛡  Hallucination Guard — API Usage Examples\n")

    try:
        httpx.get(f"{BASE_URL}/health", timeout=5).raise_for_status()
    except Exception:
        print(f"✗ Server not reachable at {BASE_URL}")
        print("  Start it with: uvicorn app.main:app --port 8000")
        sys.exit(1)

    example_health_check()
    example_single_detection()
    example_batch_analysis()


if __name__ == "__main__":
    main()
