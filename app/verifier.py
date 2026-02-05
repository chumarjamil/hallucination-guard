"""Fact Verification Engine — verifies claims against trusted sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import wikipediaapi
from sentence_transformers import SentenceTransformer, util

from app.claims import Claim

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """Result of verifying a single claim."""

    claim: Claim
    is_supported: bool = False
    confidence: float = 0.0
    evidence: Optional[str] = None
    source: Optional[str] = None
    similarity_score: float = 0.0
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Wikipedia evidence fetcher
# ---------------------------------------------------------------------------

class WikipediaSource:
    """Fetch evidence passages from Wikipedia."""

    def __init__(self, language: str = "en") -> None:
        self.wiki = wikipediaapi.Wikipedia(
            user_agent="HallucinationGuard/0.1 (https://github.com/hallucination-guard)",
            language=language,
        )

    def search(self, query: str, max_chars: int = 2000) -> Optional[str]:
        """Return the summary text for *query*, or ``None``."""
        page = self.wiki.page(query)
        if not page.exists():
            logger.debug("Wikipedia page not found for query: %s", query)
            return None
        text = page.summary[:max_chars] if page.summary else None
        logger.debug("Wikipedia hit for '%s' (%d chars)", query, len(text or ""))
        return text


# ---------------------------------------------------------------------------
# Semantic similarity scorer
# ---------------------------------------------------------------------------

class SemanticScorer:
    """Compute semantic similarity between a claim and evidence."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        logger.info("Loading sentence-transformer model '%s' …", model_name)
        self.model = SentenceTransformer(model_name)

    def score(self, claim_text: str, evidence_text: str) -> float:
        """Return cosine similarity in ``[0, 1]``."""
        embeddings = self.model.encode(
            [claim_text, evidence_text], convert_to_tensor=True
        )
        sim = util.cos_sim(embeddings[0], embeddings[1]).item()
        return float(max(0.0, min(1.0, sim)))


# ---------------------------------------------------------------------------
# Main verifier
# ---------------------------------------------------------------------------

class FactVerifier:
    """Verify a list of claims against Wikipedia + semantic similarity."""

    SUPPORT_THRESHOLD: float = 0.45

    def __init__(
        self,
        wiki_lang: str = "en",
        transformer_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.wiki = WikipediaSource(language=wiki_lang)
        self.scorer = SemanticScorer(model_name=transformer_model)

    # ---- helpers ----------------------------------------------------------

    def _search_queries(self, claim: Claim) -> List[str]:
        """Generate Wikipedia search queries from a claim."""
        queries: List[str] = []
        if claim.subject:
            queries.append(claim.subject)
        # Also try named-entity strings embedded in the claim text
        words = claim.text.split()
        for w in words:
            if w[0:1].isupper() and len(w) > 2 and w.lower() not in {
                "the", "this", "that", "these", "those", "there",
            }:
                queries.append(w)
        if not queries:
            queries.append(claim.text[:80])
        # deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique.append(q)
        return unique

    # ---- public API -------------------------------------------------------

    def verify(self, claims: List[Claim]) -> List[VerificationResult]:
        """Verify each claim and return :class:`VerificationResult` objects."""
        results: List[VerificationResult] = []

        for claim in claims:
            best_score = 0.0
            best_evidence: Optional[str] = None
            best_source: Optional[str] = None

            for query in self._search_queries(claim):
                evidence = self.wiki.search(query)
                if evidence is None:
                    continue
                sim = self.scorer.score(claim.text, evidence)
                if sim > best_score:
                    best_score = sim
                    best_evidence = evidence[:500]
                    best_source = f"Wikipedia: {query}"

            is_supported = best_score >= self.SUPPORT_THRESHOLD
            result = VerificationResult(
                claim=claim,
                is_supported=is_supported,
                confidence=best_score,
                evidence=best_evidence,
                source=best_source,
                similarity_score=best_score,
            )
            results.append(result)
            logger.info(
                "Claim verified — supported=%s  confidence=%.2f  claim='%s'",
                is_supported,
                best_score,
                claim.text[:60],
            )

        return results
