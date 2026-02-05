"""Basic usage example — detect hallucinations in AI-generated text."""

from app.detector import HallucinationDetector


def main() -> None:
    # Initialise the detector (loads spaCy + sentence-transformer models once)
    detector = HallucinationDetector()

    # --- Example 1: clearly hallucinated text --------------------------------
    text_1 = (
        "The Eiffel Tower is located in Berlin, Germany. "
        "It was built in 1920 by Leonardo da Vinci."
    )
    result_1 = detector.detect(text_1)

    print("=" * 60)
    print("EXAMPLE 1 — Hallucinated text")
    print("=" * 60)
    print(f"  Risk score     : {result_1.hallucination_risk:.2%}")
    print(f"  Confidence     : {result_1.confidence:.2%}")
    print(f"  Total claims   : {result_1.total_claims}")
    print(f"  Unsupported    : {result_1.unsupported_claims}")
    print(f"  Highlighted    : {result_1.highlighted_text}")
    for fc in result_1.flagged_claims:
        print(f"  ⚠ {fc['claim']}")
        print(f"    confidence={fc['confidence']:.4f}  source={fc.get('source', 'N/A')}")
    print()

    # --- Example 2: factually accurate text ----------------------------------
    text_2 = (
        "Python is a high-level programming language created by Guido van Rossum. "
        "It was first released in 1991."
    )
    result_2 = detector.detect(text_2)

    print("=" * 60)
    print("EXAMPLE 2 — Factual text")
    print("=" * 60)
    print(f"  Risk score     : {result_2.hallucination_risk:.2%}")
    print(f"  Confidence     : {result_2.confidence:.2%}")
    print(f"  Total claims   : {result_2.total_claims}")
    print(f"  Unsupported    : {result_2.unsupported_claims}")
    print(f"  Highlighted    : {result_2.highlighted_text}")
    if not result_2.flagged_claims:
        print("  ✓ No flagged claims — text looks factual.")
    print()

    # --- Example 3: mixed text -----------------------------------------------
    text_3 = (
        "Albert Einstein developed the theory of relativity. "
        "He also invented the smartphone in 1905."
    )
    result_3 = detector.detect(text_3)

    print("=" * 60)
    print("EXAMPLE 3 — Mixed text")
    print("=" * 60)
    print(f"  Risk score     : {result_3.hallucination_risk:.2%}")
    print(f"  Confidence     : {result_3.confidence:.2%}")
    print(f"  Flagged claims : {len(result_3.flagged_claims)}")
    print(f"  Highlighted    : {result_3.highlighted_text}")
    print()


if __name__ == "__main__":
    main()
