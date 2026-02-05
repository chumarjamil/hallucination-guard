"""
Basic SDK Usage — Hallucination Guard
======================================

Demonstrates how to use the HallucinationDetector Python SDK
to analyse AI-generated text for factual accuracy.

Run:
    python examples/basic_usage.py
"""

from __future__ import annotations

from app.detector import HallucinationDetector

SEPARATOR = "=" * 64

SAMPLES = [
    {
        "label": "Hallucinated text",
        "text": (
            "The Eiffel Tower is located in Berlin, Germany. "
            "It was built in 1920 by Leonardo da Vinci."
        ),
    },
    {
        "label": "Factual text",
        "text": (
            "Python is a high-level programming language created by Guido van Rossum. "
            "It was first released in 1991."
        ),
    },
    {
        "label": "Mixed (partial hallucination)",
        "text": (
            "Albert Einstein developed the theory of relativity. "
            "He also invented the smartphone in 1905."
        ),
    },
    {
        "label": "Fabricated history",
        "text": "The Great Wall of China was built in 1995 by NASA.",
    },
    {
        "label": "Wrong attribution",
        "text": "Microsoft was founded by Steve Jobs and Steve Wozniak in a garage in Cupertino.",
    },
]


def print_result(label: str, result) -> None:
    print(SEPARATOR)
    print(f"  {label}")
    print(SEPARATOR)
    print(f"  Hallucination risk : {result.hallucination_risk:.2%}")
    print(f"  Confidence         : {result.confidence:.2%}")
    print(f"  Claims (total)     : {result.total_claims}")
    print(f"  Supported          : {result.supported_claims}")
    print(f"  Unsupported        : {result.unsupported_claims}")
    print(f"  Avg similarity     : {result.average_similarity:.4f}")
    print()
    print(f"  Highlighted: {result.highlighted_text}")
    print()
    if result.flagged_claims:
        for i, fc in enumerate(result.flagged_claims, 1):
            print(f"  [{i}] {fc['claim']}")
            print(f"      confidence={fc['confidence']:.4f}  source={fc.get('source', 'N/A')}")
    else:
        print("  ✓ No flagged claims — text appears factual.")
    print()


def main() -> None:
    print("\n🛡  Hallucination Guard — SDK Demo\n")

    detector = HallucinationDetector()

    for sample in SAMPLES:
        result = detector.detect(sample["text"])
        print_result(sample["label"], result)


if __name__ == "__main__":
    main()
