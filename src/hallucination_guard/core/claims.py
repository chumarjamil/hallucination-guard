"""Claim Extraction Engine — extracts factual claims from raw text using NLP."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import spacy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Claim:
    """A single factual claim extracted from text."""

    text: str
    source_span: tuple[int, int] = (0, 0)
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

_FACTUAL_INDICATORS = frozenset({
    "is", "was", "are", "were", "has", "had",
    "founded", "invented", "discovered", "created", "published",
    "born", "died", "located", "contains", "produces", "consists",
    "became", "established", "developed", "introduced", "launched",
    "released", "built", "designed", "won", "received", "achieved",
    "holds", "measures", "weighs", "costs", "earned", "scored",
    "ranked", "reached", "surpassed", "exceeded", "composed",
    "flows", "empties", "borders", "spans", "covers",
})


def _looks_factual(sent_text: str) -> bool:
    tokens = sent_text.lower().split()
    return bool(_FACTUAL_INDICATORS & set(tokens))


def _has_named_entity(sent, min_entities: int = 1) -> bool:
    return len(sent.ents) >= min_entities


def _extract_svo(sent) -> tuple[Optional[str], Optional[str], Optional[str]]:
    subject = predicate = obj = None
    for token in sent:
        if "subj" in token.dep_:
            subject = token.text
        if token.dep_ == "ROOT":
            predicate = token.lemma_
        if "obj" in token.dep_ or "attr" in token.dep_:
            obj = token.text
    return subject, predicate, obj


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class ClaimExtractor:
    """Extract factual claims from text using spaCy NLP."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        try:
            self.nlp = spacy.load(model_name)
            logger.info("Loaded spaCy model '%s'", model_name)
        except OSError:
            logger.warning("spaCy model '%s' not found — downloading …", model_name)
            spacy.cli.download(model_name)  # type: ignore[attr-defined]
            self.nlp = spacy.load(model_name)

    def extract(self, text: str) -> List[Claim]:
        """Return a list of factual :class:`Claim` objects from *text*."""
        doc = self.nlp(text)
        claims: List[Claim] = []

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            if _looks_factual(sent_text) or _has_named_entity(sent):
                subj, pred, obj = _extract_svo(sent)
                claim = Claim(
                    text=sent_text,
                    source_span=(sent.start_char, sent.end_char),
                    subject=subj,
                    predicate=pred,
                    object_=obj,
                )
                claims.append(claim)
                logger.debug("Extracted claim: %s", sent_text)

        logger.info("Extracted %d claim(s) from input text", len(claims))
        return claims
