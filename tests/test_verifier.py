"""Unit tests for the Fact Verification Engine."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.claims import Claim
from app.verifier import (
    FactVerifier,
    SemanticScorer,
    VerificationResult,
    WikipediaSource,
)


# ---------------------------------------------------------------------------
# WikipediaSource
# ---------------------------------------------------------------------------

class TestWikipediaSource:
    def test_search_existing_page(self):
        wiki = WikipediaSource(language="en")
        result = wiki.search("Python (programming language)")
        # Could be None if network is down, but should not crash
        assert result is None or isinstance(result, str)

    def test_search_nonexistent_page(self):
        wiki = WikipediaSource(language="en")
        result = wiki.search("xyznonexistentpage12345678")
        assert result is None

    def test_max_chars_limit(self):
        wiki = WikipediaSource(language="en")
        result = wiki.search("Python (programming language)", max_chars=100)
        if result is not None:
            assert len(result) <= 100


# ---------------------------------------------------------------------------
# SemanticScorer
# ---------------------------------------------------------------------------

class TestSemanticScorer:
    @pytest.fixture(scope="class")
    def scorer(self):
        return SemanticScorer(model_name="all-MiniLM-L6-v2")

    def test_identical_texts_high_similarity(self, scorer: SemanticScorer):
        score = scorer.score("Python is a programming language.", "Python is a programming language.")
        assert score > 0.9

    def test_unrelated_texts_low_similarity(self, scorer: SemanticScorer):
        score = scorer.score(
            "The cat sat on the mat.",
            "Quantum physics describes subatomic particles.",
        )
        assert score < 0.5

    def test_score_in_valid_range(self, scorer: SemanticScorer):
        score = scorer.score("Hello world", "Goodbye world")
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# VerificationResult
# ---------------------------------------------------------------------------

class TestVerificationResult:
    def test_defaults(self):
        claim = Claim(text="test claim")
        vr = VerificationResult(claim=claim)
        assert vr.is_supported is False
        assert vr.confidence == 0.0
        assert vr.evidence is None


# ---------------------------------------------------------------------------
# FactVerifier (with mocked Wikipedia)
# ---------------------------------------------------------------------------

class TestFactVerifier:
    def test_verify_returns_results(self):
        with patch.object(WikipediaSource, "search", return_value="Python is a high-level programming language."):
            verifier = FactVerifier()
            claims = [Claim(text="Python is a programming language.", subject="Python")]
            results = verifier.verify(claims)
            assert len(results) == 1
            assert isinstance(results[0], VerificationResult)

    def test_verify_empty_claims(self):
        verifier = FactVerifier()
        results = verifier.verify([])
        assert results == []

    def test_unsupported_claim_when_no_wiki(self):
        with patch.object(WikipediaSource, "search", return_value=None):
            verifier = FactVerifier()
            claims = [Claim(text="Unicorns rule the world.", subject="Unicorns")]
            results = verifier.verify(claims)
            assert len(results) == 1
            assert results[0].is_supported is False
            assert results[0].confidence == 0.0

    def test_search_queries_generation(self):
        verifier = FactVerifier()
        claim = Claim(text="Albert Einstein was born in Germany.", subject="Albert")
        queries = verifier._search_queries(claim)
        assert "Albert" in queries
        assert len(queries) >= 1
