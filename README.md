<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge" alt="Status: Active">
  <img src="https://img.shields.io/github/actions/workflow/status/chumarjamil/hallucination-guard/ci.yml?branch=main&style=for-the-badge&label=CI" alt="Build Status">
  <img src="https://img.shields.io/badge/code%20style-ruff-000000?style=for-the-badge" alt="Code style: ruff">
</p>

<h1 align="center">🛡 Hallucination Guard</h1>

<p align="center">
  <strong>The open-source standard for hallucination detection in AI-generated text.</strong><br><br>
  <code>pip install hallucination-guard</code><br><br>
  Python SDK · Global CLI · REST API · LangChain / LlamaIndex Ready
</p>

---

## The Problem

LLMs hallucinate. They generate confident, fluent text that is **factually wrong** — invented dates, swapped locations, fabricated citations.

In production systems — healthcare, legal, finance, education — this is not a minor inconvenience. **It's a liability.**

There is no standard, developer-friendly tool to programmatically detect these hallucinations before they reach end users.

## The Solution

**Hallucination Guard** is a complete hallucination detection toolkit:

```
Input Text → Claim Extraction → Fact Verification → Risk Scoring → Explanation → Structured Output
```

| Feature                | Description                                        |
| ---------------------- | -------------------------------------------------- |
| **Claim Extraction**   | spaCy NLP identifies factual statements            |
| **Fact Verification**  | Wikipedia + sentence-transformer semantic matching |
| **Risk Scoring**       | Weighted formula → `0.0 – 1.0` risk score          |
| **Explanation Engine** | Human-readable explanations per claim              |
| **Text Highlighting**  | Plain-text `⚠[…]⚠` + colorized CLI output          |
| **Global CLI**         | `hallucination-guard check "text"`                 |
| **Python SDK**         | `from hallucination_guard import detect`           |
| **REST API**           | `hallucination-guard api --port 8000`              |
| **Integrations**       | LangChain, LlamaIndex, RAG, Streamlit              |
| **Docker**             | One-command deployment                             |
| **CI/CD**              | GitHub Actions (lint, type check, test, Docker)    |

---

## Quick Start

### Install

```bash
pip install hallucination-guard
```

Or from source:

```bash
git clone https://github.com/chumarjamil/hallucination-guard.git
cd hallucination-guard
pip install -e .
python -m spacy download en_core_web_sm
```

### Try It

```bash
hallucination-guard check "The Eiffel Tower is located in Berlin."
```

```python
from hallucination_guard import detect

result = detect("The Eiffel Tower is located in Berlin.")
print(result.hallucinated)     # True
print(result.confidence)       # 0.91
print(result.explanation)      # "Detected 1 unsupported claim(s) …"
```

---

## CLI

Hallucination Guard ships with a global CLI powered by Typer + Rich.

### Commands

```bash
# Check inline text
hallucination-guard check "Paris is the capital of Germany."

# Check a file
hallucination-guard file article.txt

# Batch check (JSON array of texts)
hallucination-guard batch inputs.json

# Start REST API server
hallucination-guard api --port 8000

# JSON output mode
hallucination-guard check "Some text" --json

# Verbose debug logging
hallucination-guard check "Some text" --verbose
```

### Sample Output

```
╭────────────────── 🛡  Hallucination Guard ──────────────────╮
│        72% Hallucination Risk  [HIGH]                       │
╰────────────────── confidence 28% ───────────────────────────╯
  Total claims   : 2
  Supported      : 0
  Unsupported    : 2
  Avg similarity : 0.2100

  Detected 2 unsupported claim(s) out of 2. Hallucination risk: 72%.

Highlighted Text
  ⚠[The Eiffel Tower is located in Berlin and was built in 1920.]⚠

┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Claim                                    ┃ Confidence ┃ Evidence        ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ 1  │ The Eiffel Tower is located in Berlin …  │     0.2100 │ The Eiffel …    │
└────┴─────────────────────────────────────────┴────────────┴─────────────────┘

Explanations
  🔴 [1] The Eiffel Tower is located in Berlin … [high]
      This claim could not be verified …
```

---

## Python SDK

Three top-level functions for instant integration:

### `detect(text)` — Full Pipeline

```python
from hallucination_guard import detect

result = detect("Albert Einstein invented the telephone in 1876.")

result.hallucinated         # True
result.hallucination_risk   # 0.68
result.confidence           # 0.32
result.flagged_claims       # [{"claim": "...", "confidence": 0.12, ...}]
result.explanations         # [Explanation(claim="...", severity="high", ...)]
result.highlighted_text     # "⚠[Albert Einstein invented …]⚠"
result.explanation          # "Detected 1 unsupported claim(s) …"
result.to_dict()            # Full JSON-serializable dict
```

### `score(text)` — Risk Score Only

```python
from hallucination_guard import score

risk = score("The Great Wall was built by NASA.")
print(risk)  # 0.72
```

### `explain(text)` — Structured Explanation

```python
from hallucination_guard import explain

info = explain("Mars is the largest planet in the solar system.")
# {
#   "hallucinated": True,
#   "confidence": 0.31,
#   "explanation": "Detected 1 unsupported claim(s) …",
#   "claims": [
#     {
#       "claim": "Mars is the largest planet …",
#       "hallucinated": True,
#       "confidence": 0.31,
#       "explanation": "This claim could not be verified …",
#       "severity": "medium",
#       "source": "Wikipedia: Mars"
#     }
#   ]
# }
```

### Advanced: Direct Guard Instance

```python
from hallucination_guard import HallucinationGuard

guard = HallucinationGuard(
    spacy_model="en_core_web_lg",
    transformer_model="all-mpnet-base-v2",
    wiki_lang="en",
)

result = guard.detect("Your text here.")
```

---

## REST API

### Start the Server

```bash
hallucination-guard api --port 8000
# or
uvicorn hallucination_guard.api.server:app --port 8000
```

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "version": "0.2.0"}
```

### `POST /detect`

```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "The Great Wall of China was built in 1995 by NASA."}'
```

```json
{
  "hallucinated": true,
  "hallucination_risk": 0.72,
  "confidence": 0.28,
  "total_claims": 1,
  "supported_claims": 0,
  "unsupported_claims": 1,
  "average_similarity": 0.18,
  "flagged_claims": [
    {
      "claim": "The Great Wall of China was built in 1995 by NASA.",
      "confidence": 0.18,
      "evidence": "The Great Wall of China is a series of fortifications …",
      "source": "Wikipedia: Great"
    }
  ],
  "explanations": [
    {
      "claim": "The Great Wall of China was built in 1995 by NASA.",
      "hallucinated": true,
      "confidence": 0.18,
      "explanation": "This claim could not be verified …",
      "severity": "high",
      "source": "Wikipedia: Great"
    }
  ],
  "highlighted_text": "⚠[The Great Wall of China was built in 1995 by NASA.]⚠",
  "explanation": "Detected 1 unsupported claim(s) out of 1. Hallucination risk: 72%."
}
```

### Docker

```bash
docker compose up -d
curl http://localhost:8000/health
```

---

## Integrations

Ready-to-use examples for popular AI frameworks in [`examples/`](examples/):

| Integration      | File                        | Description                      |
| ---------------- | --------------------------- | -------------------------------- |
| **LangChain**    | `langchain_integration.py`  | Post-process LLM outputs         |
| **LlamaIndex**   | `llamaindex_integration.py` | Verify RAG responses             |
| **RAG Pipeline** | `rag_pipeline.py`           | Generic `RAGGuard` wrapper class |
| **Streamlit**    | `streamlit_app.py`          | Web UI dashboard                 |
| **REST Client**  | `api_client.py`             | HTTP client example              |
| **SDK**          | `basic_usage.py`            | Python SDK patterns              |

### LangChain Example

```python
from hallucination_guard import detect

def verify_llm_output(response: str, threshold: float = 0.5) -> dict:
    result = detect(response)
    return {
        "response": response,
        "safe_to_use": result.hallucination_risk < threshold,
        "risk": result.hallucination_risk,
        "flagged": result.flagged_claims,
    }
```

### RAG Guard Pattern

```python
from hallucination_guard import detect

class RAGGuard:
    def __init__(self, rag_fn, threshold=0.5):
        self.rag_fn = rag_fn
        self.threshold = threshold

    def query(self, question: str):
        answer = self.rag_fn(question)
        result = detect(answer)
        return {
            "answer": answer,
            "safe": result.hallucination_risk < self.threshold,
            "risk": result.hallucination_risk,
        }
```

---

## Architecture

```
Input Text
    │
    ▼
┌─────────────────┐
│ Claim Extractor │  spaCy NLP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fact Verifier   │  Wikipedia + sentence-transformers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Risk Scorer     │  Weighted formula → 0.0–1.0
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Explainer       │  Human-readable explanations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Highlighter     │  ⚠[…]⚠ markers + Rich CLI
└────────┬────────┘
         │
         ▼
  DetectionResult
```

### Project Structure

```
.
├── src/hallucination_guard/
│   ├── __init__.py            # Public API: detect, score, explain
│   ├── sdk.py                 # SDK convenience functions
│   ├── cli.py                 # Typer CLI (check, file, batch, api)
│   ├── core/
│   │   ├── detector.py        # Pipeline orchestration
│   │   ├── claims.py          # Claim extraction (spaCy)
│   │   ├── verifier.py        # Fact verification (Wikipedia + SBERT)
│   │   ├── scorer.py          # Risk scoring engine
│   │   ├── explainer.py       # Explanation generation
│   │   └── highlight.py       # Text highlighting
│   ├── api/
│   │   └── server.py          # FastAPI REST server
│   └── utils/
│       └── config.py          # Env-based configuration
├── tests/                     # Unit + integration tests
├── examples/                  # Integration examples
├── docs/                      # Architecture documentation
├── .github/workflows/ci.yml   # CI pipeline
├── pyproject.toml             # Package config + tool settings
├── Dockerfile                 # Production container
├── docker-compose.yml
├── Makefile
├── CONTRIBUTING.md
└── LICENSE
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for detailed technical documentation.

---

## Configuration

All settings via environment variables or constructor arguments:

| Environment Variable                    | Default            | Description                    |
| --------------------------------------- | ------------------ | ------------------------------ |
| `HALLUCINATION_GUARD_SPACY_MODEL`       | `en_core_web_sm`   | spaCy model                    |
| `HALLUCINATION_GUARD_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | Embedding model                |
| `HALLUCINATION_GUARD_WIKI_LANG`         | `en`               | Wikipedia language             |
| `HALLUCINATION_GUARD_SUPPORT_THRESHOLD` | `0.45`             | Min similarity for "supported" |
| `HALLUCINATION_GUARD_HOST`              | `0.0.0.0`          | API bind address               |
| `HALLUCINATION_GUARD_PORT`              | `8000`             | API port                       |
| `HALLUCINATION_GUARD_LOG_LEVEL`         | `INFO`             | Logging level                  |

---

## How It Works

1. **Claim Extraction** — spaCy parses the text, identifies factual indicators (*is*, *founded*, *invented*) and named entities, extracts structured claims with SVO triples.

2. **Fact Verification** — Each claim queries Wikipedia. Evidence is compared using `all-MiniLM-L6-v2` sentence-transformer, producing cosine-similarity scores.

3. **Risk Scoring** — Weighted formula:
   - 50% unsupported claim ratio
   - 35% inverse avg similarity
   - 15% non-linear severity penalty (>50% failure)

4. **Explanation** — Each claim gets a human-readable explanation with severity rating (low/medium/high).

5. **Highlighting** — Unsupported claims wrapped in `⚠[…]⚠` markers. CLI renders bold red via Rich.

---

## Development

```bash
git clone https://github.com/chumarjamil/hallucination-guard.git
cd hallucination-guard
make dev          # editable install + dev deps + pre-commit

make test         # run tests with coverage
make lint         # ruff linter
make typecheck    # mypy
make format       # auto-format
make serve        # start API with hot-reload
make demo         # run CLI demo
make docker       # build Docker image
```

---

## Roadmap

- [x] Claim extraction + fact verification pipeline
- [x] CLI with Rich output
- [x] REST API (FastAPI)
- [x] Python SDK (`detect`, `score`, `explain`)
- [x] Explanation engine with severity ratings
- [x] Docker + docker-compose
- [x] CI/CD (GitHub Actions)
- [x] Integration examples (LangChain, LlamaIndex, RAG, Streamlit)
- [ ] LLM-based claim extraction (GPT / Ollama / local)
- [ ] Multi-source verification (Wikidata, PubMed, Knowledge Graph)
- [ ] Async pipeline for concurrent verification
- [ ] Caching layer (Redis / SQLite)
- [ ] Custom knowledge bases
- [ ] Web UI dashboard
- [ ] PyPI package distribution
- [ ] Prometheus metrics export
- [ ] API key authentication
- [ ] Confidence calibration with labeled datasets
- [ ] Webhook notifications for flagged content

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, and PR guidelines.

```bash
make dev && make test
```

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <strong>Built for developers who ship AI responsibly.</strong><br>
  <sub>If this helps you, consider giving it a ⭐</sub>
</p>
