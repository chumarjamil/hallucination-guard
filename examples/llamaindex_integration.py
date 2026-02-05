"""
LlamaIndex Integration — Hallucination Guard
==============================================

Use Hallucination Guard to verify RAG pipeline outputs from LlamaIndex
before presenting them to users.

Requirements:
    pip install llama-index hallucination-guard

Usage:
    python examples/llamaindex_integration.py
"""

from __future__ import annotations

from hallucination_guard import detect, score


def verify_rag_response(query: str, response: str, threshold: float = 0.5) -> dict:
    """Verify a RAG pipeline response for hallucinations.

    Args:
        query: The original user query.
        response: The RAG pipeline's generated response.
        threshold: Risk threshold above which to flag the response.

    Returns:
        Verification result dict.
    """
    result = detect(response)

    return {
        "query": query,
        "response": response,
        "hallucinated": result.hallucinated,
        "risk": result.hallucination_risk,
        "confidence": result.confidence,
        "flagged_claims": result.flagged_claims,
        "explanation": result.explanation,
        "safe_to_use": result.hallucination_risk < threshold,
        "highlighted": result.highlighted_text,
    }


EXAMPLE_PATTERN = """
# In a real LlamaIndex pipeline:

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

response = query_engine.query("What is the capital of France?")

# Verify before returning to user
verification = verify_rag_response(
    query="What is the capital of France?",
    response=str(response),
)

if not verification["safe_to_use"]:
    # Fall back to a safer response or add a disclaimer
    print("⚠ Response may contain inaccuracies")
"""


def main() -> None:
    print("🛡  Hallucination Guard × LlamaIndex Integration\n")

    # Simulated RAG response
    query = "Tell me about the history of Python programming language"
    response = (
        "Python was created by Guido van Rossum and first released in 1991. "
        "It was developed at Microsoft Research in Seattle."
    )

    print(f"Query:    {query}")
    print(f"Response: {response}\n")

    verification = verify_rag_response(query, response)

    print(f"Hallucinated: {verification['hallucinated']}")
    print(f"Risk:         {verification['risk']:.2%}")
    print(f"Safe to use:  {verification['safe_to_use']}")
    print(f"Highlighted:  {verification['highlighted']}")

    # Quick score-only check
    risk = score(response)
    print(f"\nQuick score:  {risk:.2%}")

    print(f"\n--- Usage pattern ---{EXAMPLE_PATTERN}")


if __name__ == "__main__":
    main()
