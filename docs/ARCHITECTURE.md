# Architecture

Detailed technical documentation for Hallucination Guard.

---

## Pipeline Overview

```
Input Text
    │
    ▼
┌─────────────────┐
│ Claim Extractor  │  app/claims.py
│ (spaCy NLP)      │
└────────┬────────┘
         │  List[Claim]
         ▼
┌─────────────────┐
│ Fact Verifier    │  app/verifier.py
│ (Wikipedia +     │
│  SBERT)          │
└────────┬────────┘
         │  List[VerificationResult]
         ▼
┌─────────────────┐
│ Risk Scorer      │  app/scorer.py
│ (weighted        │
│  formula)        │
└────────┬────────┘
         │  RiskReport
         ▼
┌─────────────────┐
│ Highlighter      │  app/highlight.py
│ (plain + Rich)   │
└────────┬────────┘
         │
         ▼
    DetectionResult
```

---

## Module Details

### 1. Claim Extraction (`app/claims.py`)

**Input**: Raw text string
**Output**: `List[Claim]`

The extractor uses spaCy to:
- Segment text into sentences
- Identify factual indicators (verbs like *is*, *was*, *founded*, *invented*)
- Detect named entities (people, places, organizations, dates)
- Extract rudimentary Subject-Verb-Object triples

A sentence is kept as a claim if it contains a factual indicator verb **or** at least one named entity.

### 2. Fact Verification (`app/verifier.py`)

**Input**: `List[Claim]`
**Output**: `List[VerificationResult]`

For each claim:
1. Generate search queries from the claim's subject and capitalized words
2. Fetch Wikipedia article summaries for each query
3. Compute cosine similarity between claim text and evidence using `sentence-transformers` (`all-MiniLM-L6-v2`)
4. Keep the best-scoring evidence passage
5. Mark the claim as **supported** if similarity ≥ threshold (default: `0.45`)

### 3. Risk Scoring (`app/scorer.py`)

**Input**: `List[VerificationResult]`
**Output**: `RiskReport`

The hallucination risk score (0.0 – 1.0) is computed as:

```
risk = 0.50 × unsupported_ratio
     + 0.35 × (1 − avg_similarity)
     + 0.15 × severity_penalty
```

Where:
- `unsupported_ratio` = unsupported claims / total claims
- `avg_similarity` = mean similarity score across all claims
- `severity_penalty` = non-linear penalty when >50% of claims fail (capped at 1.0)

### 4. Highlighting (`app/highlight.py`)

**Input**: Original text + `RiskReport`
**Output**: Highlighted text

Two output modes:
- **Plain text**: Unsupported claims wrapped in `⚠[…]⚠` markers
- **Rich CLI**: Bold red styling on unsupported claim spans using Rich library

### 5. Detector (`app/detector.py`)

Orchestration layer that chains all four stages. This is the primary SDK entry-point.

```python
detector = HallucinationDetector()
result = detector.detect("Some text")
# result.hallucination_risk  → float
# result.flagged_claims      → list of dicts
# result.highlighted_text    → str
```

### 6. API Server (`app/main.py`)

FastAPI application with:
- `GET /health` — readiness check
- `POST /detect` — full detection pipeline

Models are loaded once during application startup via the lifespan context manager.

### 7. Configuration (`app/config.py`)

Frozen dataclass reading from `HALLUCINATION_GUARD_*` environment variables with sensible defaults. All settings are documented in the README.

---

## Data Flow

```
                    ┌──────────┐
                    │  Client  │
                    └────┬─────┘
                         │
              ┌──────────▼──────────┐
              │   CLI / API / SDK   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  HallucinationDetector │
              │  (detector.py)      │
              └──┬─────┬─────┬──┬──┘
                 │     │     │  │
    ┌────────────▼┐ ┌──▼──┐ ┌▼──▼────┐
    │ ClaimExtract│ │Fact │ │ Risk   │
    │ or          │ │Veri │ │ Scorer │
    │             │ │fier │ │        │
    └─────────────┘ └──┬──┘ └───┬────┘
                       │        │
              ┌────────▼────────▼───┐
              │   Highlighter       │
              └─────────┬───────────┘
                        │
              ┌─────────▼───────────┐
              │   DetectionResult   │
              └─────────────────────┘
```

---

## Key Design Decisions

| Decision | Rationale |
| --- | --- |
| spaCy for NLP | Fast, well-maintained, no API key needed |
| Wikipedia as source | Free, reliable, broad coverage |
| sentence-transformers | Local inference, no API costs, good accuracy |
| Weighted scoring formula | Tunable, interpretable, no black box |
| Dataclasses over Pydantic (internal) | Lighter weight for internal data flow |
| Pydantic for API schemas | Automatic validation, OpenAPI docs |
| Rich for CLI | Professional output with minimal code |
| Environment variable config | 12-factor app compliance, Docker-friendly |
