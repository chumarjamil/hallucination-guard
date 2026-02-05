"""Example API client — demonstrates how to call the REST API programmatically."""

from __future__ import annotations

import json
import sys

import httpx


BASE_URL = "http://localhost:8000"


def check_health() -> None:
    resp = httpx.get(f"{BASE_URL}/health")
    resp.raise_for_status()
    print("Health:", resp.json())


def detect(text: str) -> dict:
    resp = httpx.post(f"{BASE_URL}/detect", json={"text": text}, timeout=120)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    check_health()

    samples = [
        "The Great Wall of China was built in 1995 by NASA.",
        "Water is composed of hydrogen and oxygen atoms.",
        "The Amazon River flows through the Sahara Desert and empties into the Pacific Ocean.",
    ]

    for text in samples:
        print("\n" + "=" * 60)
        print(f"INPUT: {text}")
        print("=" * 60)
        result = detect(text)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
