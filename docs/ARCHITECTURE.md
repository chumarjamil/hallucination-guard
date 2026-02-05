# Architecture

Detailed technical documentation for Hallucination Guard.

---

## Pipeline Overview

```
Input Text
    │
    ▼
┌──────────────────┐
│ Claim Extractor   │  core/claims.py
│ (spaCy NLP)       │
└────────┬─────────┘
         │  List[Claim]
         ▼
┌──────────────────┐
│ Fact Verifier     │  core/verifier.py
│ (Wikipedia +      │
│  SBERT)           │
└────────┬─────────┘
         │  List[VerificationResult]
         ▼
┌──────────────────┐
│ Risk Scorer       │  core/scorer.py
│ (weighted formula)│
└────────┬─────────┘
         │  RiskReport
         ▼
┌──────────────────┐
│ Explainer         │  core/explainer.py
│ (human-readable)  │
└────────┬─────────┘
         │  List[Explanation]
         ▼
┌──────────────────┐
│ Highlighter       │  core/highlight.py
│ (plain + Rich)    │
└────────┬─────────┘
         │
         ▼
    DetectionResult
```

---

## Module Details

### 1. Claim Extraction (`core/claims.py`)

**Input**: Raw text string
**Output**: `List[Claim]`

The extractor uses spaCy to:
- Segment text into sentences
- Identify factual indicators (verbs like *is*, *was*, *founded*, *invented*)
- Detect named entities (people, places, organizations, dates)
- Extract rudimentary Subject-Verb-Object triples

A sentence is kept as a claim if it contains a factual indicator verb **or** at least one named entity.

### 2. Fact Verification (`core/verifier.py`)

**Input**: `List[Claim]`
**Output**: `List[VerificationResult]`

For each claim:
1. Generate search queries from the claim's subject and capitalized words
2. Fetch Wikipedia article summaries for each query
3. Compute cosine similarity between claim text and evidence using `sentence-transformers` (`all-MiniLM-L6-v2`)
4. Keep the best-scoring evidence passage
5. Mark the claim as **supported** if similarity >= threshold (default: `0.45`)

### 3. Risk Scoring (`core/scorer.py`)

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

### 4. Explanation Generation (`core/explainer.py`)

**Input**: `List[VerificationResult]`
**Output**: `List[Explanation]`

Generates human-readable explanations for each claim:
- Supported claims get a "factually supported" message
- Unsupported claims with evidence get a "could not be verified" message with contradicting source
- Unsupported claims without evidence get a "no supporting evidence found" message

Each explanation includes a severity rating: **low**, **medium**, or **high**.

### 5. Highlighting (`core/highlight.py`)

**Input**: Original text + `RiskReport`
**Output**: Highlighted text

Two output modes:
- **Plain text**: Unsupported claims wrapped in `⚠[…]⚠` markers
- **Rich CLI**: Bold red styling on unsupported claim spans using Rich library

### 6. Detector (`core/detector.py`)

Orchestration layer that chains all five stages. Primary SDK entry-point.

```python
from hallucination_guard import HallucinationGuard

guard = HallucinationGuard()
result = guard.detect("Some text")
# result.hallucinated          → bool
# result.hallucination_risk    → float
# result.flagged_claims        → list of dicts
# result.explanations          → list of Explanation
# result.highlighted_text      → str
# result.explanation           → str (summary)
# result.to_dict()             → dict (JSON-safe)
```

### 7. SDK (`sdk.py`)

Three convenience functions wrapping `HallucinationGuard`:

```python
from hallucination_guard import detect, score, explain

result = detect("text")   # DetectionResult
risk   = score("text")    # float
info   = explain("text")  # dict
```

Uses a lazy singleton — the guard is created on first call and reused.

### 8. CLI (`cli.py`)

Typer-based CLI with four commands:
- `check` — inline text analysis
- `file` — analyse a text file
- `batch` — batch-process a JSON array
- `api` — start the REST API server

Rich output with colored panels, tables, and per-claim explanations.

### 9. API Server (`api/server.py`)

FastAPI application with:
- `GET /health` — readiness check
- `POST /detect` — full detection pipeline with explanations

Models are loaded once during application startup via the lifespan context manager.

### 10. Configuration (`utils/config.py`)

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
              │  HallucinationGuard │
              │  (core/detector.py) │
              └──┬───┬───┬───┬───┬─┘
                 │   │   │   │   │
    ┌────────────▼┐ ┌▼───▼┐ ┌▼───▼──────┐
    │ ClaimExtract│ │Fact │ │ Scorer    │
    │ or          │ │Veri │ │           │
    │             │ │fier │ │           │
    └─────────────┘ └──┬──┘ └───┬───────┘
                       │        │
              ┌────────▼────────▼───┐
              │     Explainer       │
              └─────────┬───────────┘
                        │
              ┌─────────▼───────────┐
              │     Highlighter     │
              └─────────┬───────────┘
                        │
              ┌─────────▼───────────┐
              │   DetectionResult   │
              └─────────────────────┘
```

---

## Package Structure

```
src/hallucination_guard/
├── __init__.py         # Public API: detect, score, explain, HallucinationGuard
├── sdk.py              # Convenience wrappers (lazy singleton)
├── cli.py              # Typer CLI (check, file, batch, api, version)
├── core/
│   ├── detector.py     # Pipeline orchestration
│   ├── claims.py       # Claim extraction (spaCy)
│   ├── verifier.py     # Fact verification (Wikipedia + SBERT)
│   ├── scorer.py       # Risk scoring
│   ├── explainer.py    # Explanation generation
│   └── highlight.py    # Text highlighting
├── api/
│   └── server.py       # FastAPI REST server
└── utils/
    └── config.py       # Env-based settings
```

---

## Key Design Decisions

| Decision                    | Rationale                                          |
| --------------------------- | -------------------------------------------------- |
| `src/` layout               | Standard Python packaging, avoids import confusion |
| Typer for CLI               | Modern, auto-generated help, type-safe             |
| spaCy for NLP               | Fast, well-maintained, no API key needed           |
| Wikipedia as source         | Free, reliable, broad coverage                     |
| sentence-transformers       | Local inference, no API costs, good accuracy       |
| Weighted scoring formula    | Tunable, interpretable, no black box               |
| Explanation engine          | Human-readable output, severity ratings            |
| Lazy SDK singleton          | Fast import, models loaded only when needed        |
| Dataclasses (internal)      | Lighter weight for internal data flow              |
| Pydantic (API schemas)      | Automatic validation, OpenAPI docs                 |
| Rich for CLI output         | Professional output with minimal code              |
| Environment variable config | 12-factor app compliance, Docker-friendly          |
| `to_dict()` on result       | Easy JSON serialization for any consumer           |
