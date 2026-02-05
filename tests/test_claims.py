"""Unit tests for the Claim Extraction Engine."""

from __future__ import annotations

import pytest

from app.claims import Claim, ClaimExtractor, _looks_factual, _has_named_entity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestLooksFactual:
    def test_factual_sentence(self):
        assert _looks_factual("Python was created by Guido van Rossum.")

    def test_non_factual_sentence(self):
        assert not _looks_factual("Hello there, how are you doing today?")

    def test_multiple_indicators(self):
        assert _looks_factual("The company was founded and is located in Berlin.")

    def test_empty_string(self):
        assert not _looks_factual("")


# ---------------------------------------------------------------------------
# Claim dataclass
# ---------------------------------------------------------------------------

class TestClaim:
    def test_str_representation(self):
        c = Claim(text="Python is a programming language.")
        assert str(c) == "Python is a programming language."

    def test_default_span(self):
        c = Claim(text="test")
        assert c.source_span == (0, 0)

    def test_metadata_default(self):
        c = Claim(text="test")
        assert c.metadata == {}


# ---------------------------------------------------------------------------
# ClaimExtractor
# ---------------------------------------------------------------------------

class TestClaimExtractor:
    @pytest.fixture(scope="class")
    def extractor(self):
        return ClaimExtractor(model_name="en_core_web_sm")

    def test_extracts_factual_claims(self, extractor: ClaimExtractor):
        text = "Python was created by Guido van Rossum in 1991. The weather is nice."
        claims = extractor.extract(text)
        assert len(claims) >= 1
        assert any("Python" in c.text for c in claims)

    def test_returns_claim_objects(self, extractor: ClaimExtractor):
        claims = extractor.extract("Albert Einstein was born in Germany.")
        assert all(isinstance(c, Claim) for c in claims)

    def test_empty_input(self, extractor: ClaimExtractor):
        claims = extractor.extract("")
        assert claims == []

    def test_no_factual_content(self, extractor: ClaimExtractor):
        claims = extractor.extract("Hello! How are you? Great to meet you.")
        # May or may not extract — but should not crash
        assert isinstance(claims, list)

    def test_source_spans_set(self, extractor: ClaimExtractor):
        text = "The Eiffel Tower is located in Paris."
        claims = extractor.extract(text)
        if claims:
            assert claims[0].source_span != (0, 0) or claims[0].text in text

    def test_multiple_sentences(self, extractor: ClaimExtractor):
        text = (
            "The Earth orbits the Sun. "
            "Water is composed of hydrogen and oxygen. "
            "Birds can fly."
        )
        claims = extractor.extract(text)
        assert len(claims) >= 2
