"""FastAPI REST API server for Hallucination Guard."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.detector import HallucinationDetector

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, description="AI-generated text to analyse.")


class FlaggedClaim(BaseModel):
    claim: str
    confidence: float
    evidence: str
    source: Optional[str] = None


class DetectResponse(BaseModel):
    hallucination_risk: float
    confidence: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    average_similarity: float
    flagged_claims: List[FlaggedClaim]
    highlighted_text: str


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Application lifespan — initialise heavy models once
# ---------------------------------------------------------------------------

_detector: Optional[HallucinationDetector] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _detector
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    logger.info("Loading models …")
    _detector = HallucinationDetector()
    logger.info("Models loaded — server ready.")
    yield
    _detector = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hallucination Guard",
    description="Detect hallucinations in AI-generated text.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/detect", response_model=DetectResponse)
async def detect(request: DetectRequest):
    if _detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialised.")
    try:
        result = _detector.detect(request.text)
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

    return DetectResponse(
        hallucination_risk=result.hallucination_risk,
        confidence=result.confidence,
        total_claims=result.total_claims,
        supported_claims=result.supported_claims,
        unsupported_claims=result.unsupported_claims,
        average_similarity=result.average_similarity,
        flagged_claims=flagged,
        highlighted_text=result.highlighted_text,
    )
