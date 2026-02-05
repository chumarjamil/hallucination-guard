"""
Hallucination Guard — Production-grade FastAPI REST API.

Features:
- Single + batch detection endpoints
- Optional API key authentication
- Rate limiting
- Metrics endpoint (/metrics)
- Structured JSON logging
- CORS support
- OpenAPI docs at /docs
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from hallucination_guard import __version__
from hallucination_guard.core.detector import HallucinationGuard

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, description="AI-generated text to analyse.")


class BatchDetectRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, description="List of texts to analyse.")


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


class BatchDetectResponse(BaseModel):
    results: List[DetectResponse]
    total: int
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool


class MetricsResponse(BaseModel):
    total_requests: int
    total_detections: int
    total_batch_detections: int
    avg_latency_ms: float
    total_claims_analysed: int
    total_hallucinations_detected: int
    uptime_seconds: float


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_guard: Optional[HallucinationGuard] = None
_start_time: float = 0.0
_metrics: Dict[str, float] = defaultdict(float)

# ---------------------------------------------------------------------------
# Auth (optional — set HALLUCINATION_GUARD_API_KEY env var to enable)
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_configured_api_key = os.getenv("HALLUCINATION_GUARD_API_KEY", "")


async def _verify_api_key(api_key: Optional[str] = Security(_api_key_header)) -> None:
    if not _configured_api_key:
        return  # auth disabled
    if api_key != _configured_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory, per-IP)
# ---------------------------------------------------------------------------

_rate_limit_max = int(os.getenv("HALLUCINATION_GUARD_RATE_LIMIT", "60"))
_rate_window = 60.0  # seconds
_rate_store: Dict[str, list] = defaultdict(list)


async def _rate_limit(request: Request) -> None:
    if _rate_limit_max <= 0:
        return
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if now - t < _rate_window]
    if len(_rate_store[client_ip]) >= _rate_limit_max:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    _rate_store[client_ip].append(now)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _guard, _start_time
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s │ %(name)s │ %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.info("Loading models …")
    _guard = HallucinationGuard()
    _start_time = time.time()
    auth_status = "enabled" if _configured_api_key else "disabled"
    logger.info("Models loaded — server ready (auth=%s, rate_limit=%d/min)", auth_status, _rate_limit_max)
    yield
    _guard = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hallucination Guard API",
    description="Production-grade hallucination detection for AI-generated text.",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_response(result) -> DetectResponse:
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__, model_loaded=_guard is not None)


@app.get("/metrics", response_model=MetricsResponse, tags=["System"])
async def metrics():
    """Server metrics endpoint."""
    total_req = int(_metrics["total_requests"])
    total_det = int(_metrics["total_detections"])
    avg_lat = (_metrics["total_latency_ms"] / total_det) if total_det else 0.0
    return MetricsResponse(
        total_requests=total_req,
        total_detections=total_det,
        total_batch_detections=int(_metrics["total_batch_detections"]),
        avg_latency_ms=round(avg_lat, 2),
        total_claims_analysed=int(_metrics["total_claims"]),
        total_hallucinations_detected=int(_metrics["total_hallucinations"]),
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@app.post("/detect", response_model=DetectResponse, tags=["Detection"],
          dependencies=[Depends(_rate_limit), Depends(_verify_api_key)])
async def detect(request: DetectRequest):
    """Detect hallucinations in a single text."""
    if _guard is None:
        raise HTTPException(status_code=503, detail="Detector not initialised.")

    _metrics["total_requests"] += 1
    t0 = time.perf_counter()

    try:
        result = _guard.detect(request.text)
    except Exception as exc:
        logger.exception("Detection failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = (time.perf_counter() - t0) * 1000
    _metrics["total_detections"] += 1
    _metrics["total_latency_ms"] += elapsed_ms
    _metrics["total_claims"] += result.total_claims
    _metrics["total_hallucinations"] += result.unsupported_claims

    logger.info("detect risk=%.2f claims=%d latency=%.0fms", result.hallucination_risk, result.total_claims, elapsed_ms)

    return _build_response(result)


@app.post("/detect/batch", response_model=BatchDetectResponse, tags=["Detection"],
          dependencies=[Depends(_rate_limit), Depends(_verify_api_key)])
async def detect_batch(request: BatchDetectRequest):
    """Batch-detect hallucinations in multiple texts."""
    if _guard is None:
        raise HTTPException(status_code=503, detail="Detector not initialised.")

    _metrics["total_requests"] += 1
    _metrics["total_batch_detections"] += 1
    t0 = time.perf_counter()

    responses: List[DetectResponse] = []
    try:
        for text in request.texts:
            result = _guard.detect(text)
            _metrics["total_detections"] += 1
            _metrics["total_claims"] += result.total_claims
            _metrics["total_hallucinations"] += result.unsupported_claims
            responses.append(_build_response(result))
    except Exception as exc:
        logger.exception("Batch detection failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = (time.perf_counter() - t0) * 1000
    _metrics["total_latency_ms"] += elapsed_ms

    logger.info("batch count=%d latency=%.0fms", len(request.texts), elapsed_ms)

    return BatchDetectResponse(
        results=responses,
        total=len(responses),
        processing_time_ms=round(elapsed_ms, 2),
    )
