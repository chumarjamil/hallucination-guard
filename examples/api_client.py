"""
REST API Usage — Hallucination Guard
======================================

Demonstrates how to call the Hallucination Guard REST API
from any HTTP client. Uses httpx for async-friendly requests.

Prerequisites:
    1. Start the API server:
       uvicorn app.main:app --host 0.0.0.0 --port 8000

    2. Install httpx:
       pip install httpx

Run:
    python examples/api_client.py
"""

from __future__ import annotations

import json
import sys

import httpx

BASE_URL = "http://localhost:8000"
SEPARATOR = "=" * 64

SAMPLES = [
    "The Great Wall of China was built in 1995 by NASA.",
    "Water is composed of hydrogen and oxygen atoms.",
    "The Amazon River flows through the Sahara Desert and empties into the Pacific Ocean.",
    "Python was created by Guido van Rossum and first released in 1991.",
    "Microsoft was founded by Steve Jobs and Steve Wozniak in a garage in Cupertino.",
]


def check_health() -> bool:
    """Verify the API server is running."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print(f"✓ Server healthy — version {data.get('version', 'unknown')}")
        return True
    except httpx.ConnectError:
        print(f"✗ Cannot connect to {BASE_URL}")
        print("  Start the server: uvicorn app.main:app --port 8000")
        return False
    except Exception as exc:
        print(f"✗ Health check failed: {exc}")
        return False


def detect(text: str) -> dict | None:
    """Send text to the /detect endpoint and return the response."""
    try:
        resp = httpx.post(
            f"{BASE_URL}/detect",
            json={"text": text},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"  ✗ Request failed: {exc}")
        return None


def main() -> None:
    print(f"\n🛡  Hallucination Guard — API Demo\n")

    if not check_health():
        sys.exit(1)

    for text in SAMPLES:
        print(f"\n{SEPARATOR}")
        print(f"  INPUT: {text}")
        print(SEPARATOR)

        result = detect(text)
        if result is None:
            continue

        risk = result["hallucination_risk"]
        label = "HIGH" if risk > 0.6 else ("MEDIUM" if risk > 0.3 else "LOW")

        print(f"  Risk: {risk:.2%} [{label}]")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Claims: {result['total_claims']} total, "
              f"{result['unsupported_claims']} unsupported")

        if result["flagged_claims"]:
            print("  Flagged:")
            for fc in result["flagged_claims"]:
                print(f"    - {fc['claim']}")
                print(f"      confidence={fc['confidence']:.4f}")

        print(f"  Highlighted: {result['highlighted_text']}")

    print()


if __name__ == "__main__":
    main()
