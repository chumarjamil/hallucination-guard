"""FastAPI REST API server for Hallucination Guard."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from hallucination_guard import __version__
from hallucination_guard.core.detector import HallucinationGuard

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, description="AI-generated text to analyse.")


class ExplanationItem(BaseModel):
    claim: str
    hallucinated: bool
    confidence: float
    explanation: str
    severity: str
    source: Optional[str] = None


class FlaggedClaim(BaseModel):
    claim: str
    confidence: float
    evidence: str
    source: Optional[str] = None


class DetectResponse(BaseModel):
    hallucinated: bool
    hallucination_risk: float
    confidence: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    flagged_claims: List[FlaggedClaim]
    explanations: List[ExplanationItem]
    highlighted_text: str
    explanation: str


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Lifespan — load models once
# ---------------------------------------------------------------------------

_guard: Optional[HallucinationGuard] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _guard
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    logger.info("Loading models …")
    _guard = HallucinationGuard()
    logger.info("Models loaded — server ready.")
    yield
    _guard = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hallucination Guard",
    description="Detect hallucinations in AI-generated text.",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version=__version__)


@app.post("/detect", response_model=DetectResponse)
async def detect(request: DetectRequest):
    if _guard is None:
        raise HTTPException(status_code=503, detail="Detector not initialised.")
    try:
        result = _guard.detect(request.text)
    except Exception as exc:
        logger.exception("Detection failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    flagged = [
        FlaggedClaim(
            claim=fc["claim"],
            confidence=fc["confidence"],
            evidence=fc["evidence"],
            source=fc.get("source"),
        )
        for fc in result.flagged_claims
    ]

    explanations = [
        ExplanationItem(
            claim=e.claim,
            hallucinated=e.hallucinated,
            confidence=e.confidence,
            explanation=e.explanation,
            severity=e.severity,
            source=e.source,
        )
        for e in result.explanations
    ]

    return DetectResponse(
        hallucinated=result.hallucinated,
        hallucination_risk=result.hallucination_risk,
        confidence=result.confidence,
        total_claims=result.total_claims,
        supported_claims=result.supported_claims,
        unsupported_claims=result.unsupported_claims,
        average_similarity=result.average_similarity,
        flagged_claims=flagged,
        explanations=explanations,
        highlighted_text=result.highlighted_text,
        explanation=result.explanation,
    )
