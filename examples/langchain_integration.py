"""
LangChain Integration — Hallucination Guard
=============================================

Use Hallucination Guard as a post-processing step in a LangChain pipeline
to verify LLM outputs before returning them to users.

Requirements:
    pip install langchain langchain-openai hallucination-guard

Usage:
    export OPENAI_API_KEY="sk-..."
    python examples/langchain_integration.py
"""

from __future__ import annotations

from hallucination_guard import detect


def verify_llm_output(llm_response: str, threshold: float = 0.5) -> dict:
    """Run hallucination detection on an LLM response.

    Returns a dict with the original response, risk assessment,
    and a cleaned version if hallucinations are detected.
    """
    result = detect(llm_response)

    return {
        "original_response": llm_response,
        "hallucinated": result.hallucinated,
        "risk": result.hallucination_risk,
        "confidence": result.confidence,
        "flagged_claims": result.flagged_claims,
        "explanation": result.explanation,
        "safe_to_use": result.hallucination_risk < threshold,
    }


# ---------------------------------------------------------------------------
# Example: LangChain chain with hallucination guard
# ---------------------------------------------------------------------------

EXAMPLE_CHAIN = """
# In a real LangChain pipeline:

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

llm = ChatOpenAI(model="gpt-4")
response = llm.invoke([HumanMessage(content="Tell me about the Eiffel Tower")])

# Verify the output
verification = verify_llm_output(response.content)

if verification["safe_to_use"]:
    print("✓ Response is factually sound")
    print(response.content)
else:
    print(f"⚠ Hallucination risk: {verification['risk']:.0%}")
    for claim in verification["flagged_claims"]:
        print(f"  - {claim['claim']}")
"""


def main() -> None:
    print("🛡  Hallucination Guard × LangChain Integration\n")

    # Simulated LLM response with a hallucination
    simulated_response = (
        "The Eiffel Tower is located in Berlin, Germany. "
        "It was designed by Gustave Eiffel and completed in 1889."
    )

    print(f"LLM Response: {simulated_response}\n")

    verification = verify_llm_output(simulated_response)

    print(f"Hallucinated: {verification['hallucinated']}")
    print(f"Risk:         {verification['risk']:.2%}")
    print(f"Safe to use:  {verification['safe_to_use']}")
    print(f"Explanation:  {verification['explanation']}")

    if verification["flagged_claims"]:
        print("\nFlagged claims:")
        for fc in verification["flagged_claims"]:
            print(f"  ⚠ {fc['claim']}")

    print(f"\n--- Usage pattern ---{EXAMPLE_CHAIN}")


if __name__ == "__main__":
    main()
