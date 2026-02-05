<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License: MIT">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=flat-square" alt="Status: Active">
  <img src="https://img.shields.io/github/actions/workflow/status/chumarjamil/hallucination-guard/ci.yml?branch=main&style=flat-square&label=CI" alt="Build Status">
  <img src="https://img.shields.io/badge/code%20style-ruff-000000?style=flat-square" alt="Code style: ruff">
</p>

<h1 align="center">🛡 Hallucination Guard</h1>

<p align="center">
  <strong>Open-source hallucination detection for AI-generated text.</strong><br>
  Extract claims. Verify facts. Score risk. Highlight problems.<br>
  Python SDK · CLI · REST API
</p>

---

## The Problem

LLMs hallucinate. They generate confident, fluent text that is **factually wrong** — invented dates, swapped locations, fabricated citations. In production systems (healthcare, legal, finance, education), this is not a minor inconvenience. It's a liability.

There is no standard, developer-friendly tool to **programmatically detect** these hallucinations before they reach end users.

## The Solution

**Hallucination Guard** is a Python toolkit that:

1. **Extracts** factual claims from any text using NLP
2. **Verifies** each claim against Wikipedia + semantic similarity
3. **Scores** overall hallucination risk on a `0.0 – 1.0` scale
4. **Highlights** unsupported claims in the original text

Use it as a **Python library**, a **CLI tool**, or a **REST API**.

---

## Features

- **Claim Extraction** — spaCy-powered NLP pipeline identifies factual statements
- **Fact Verification** — Wikipedia API + sentence-transformer semantic matching
- **Risk Scoring** — Weighted formula combining claim failure rate, confidence, and severity
- **Text Highlighting** — Plain-text markers (`⚠[…]⚠`) + colorized Rich CLI output
- **REST API** — FastAPI server with `POST /detect` endpoint
- **CLI** — One-command analysis with formatted tables and color output
- **Python SDK** — Three lines of code to integrate into any pipeline
- **Configurable** — Environment variables or constructor arguments
- **Containerized** — Docker + docker-compose for one-command deployment
- **CI/CD** — GitHub Actions pipeline (lint, typecheck, test, Docker build)

---

## Demo

### CLI

```bash
$ python cli.py "The Eiffel Tower is located in Berlin and was built in 1920."
```

```
╭─────────────────── Hallucination Guard ───────────────────╮
│          Hallucination Risk: 72.00%                       │
╰─────────────────── confidence 28.00% ────────────────────╯
  Total claims   : 2
  Supported      : 0
  Unsupported    : 2
  Avg similarity : 0.2100

Highlighted Text
⚠[The Eiffel Tower is located in Berlin and was built in 1920.]⚠

┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Claim                                       ┃ Confidence ┃ Evidence                       ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ The Eiffel Tower is located in Berlin and   │     0.2100 │ The Eiffel Tower is a wrought- │
│    │ was built in 1920.                           │            │ iron lattice tower on the      │
│    │                                              │            │ Champ de Mars in Paris, France │
└────┴──────────────────────────────────────────────┴────────────┴────────────────────────────────┘
```

### API

```bash
$ curl -X POST http://localhost:8000/detect \
    -H "Content-Type: application/json" \
    -d '{"text": "The Great Wall of China was built in 1995 by NASA."}'
```

```json
{
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
  "highlighted_text": "⚠[The Great Wall of China was built in 1995 by NASA.]⚠"
}
```

### Python SDK

```python
from app.detector import HallucinationDetector

detector = HallucinationDetector()
result = detector.detect("Albert Einstein invented the telephone in 1876.")

print(result.hallucination_risk)   # 0.68
print(result.flagged_claims)       # [{"claim": "...", "confidence": 0.12, ...}]
print(result.highlighted_text)     # "⚠[Albert Einstein invented …]⚠"
```

---

## Installation

### Quick Start

```bash
git clone https://github.com/chumarjamil/hallucination-guard.git
cd hallucination-guard
python -m venv .venv
source .venv/bin/activate
make install
```

### Manual

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Docker

```bash
docker compose up -d
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}
```

---

## Usage

### CLI

```bash
# Inline text
python cli.py "The Eiffel Tower is located in Berlin."

# From file
python cli.py --file article.txt

# Pipe from stdin
echo "Python was invented by mass of Guido." | python cli.py

# Verbose logging
python cli.py -v "Some AI text here."
```

### REST API

```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health

# Detect hallucinations
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Your AI-generated text here."}'
```

### Python SDK

```python
from app.detector import HallucinationDetector

detector = HallucinationDetector(
    spacy_model="en_core_web_sm",
    transformer_model="all-MiniLM-L6-v2",
    wiki_lang="en",
)

result = detector.detect("Some AI-generated text.")

print(result.hallucination_risk)    # float 0.0–1.0
print(result.confidence)            # float 0.0–1.0
print(result.flagged_claims)        # list of dicts
print(result.highlighted_text)      # str with ⚠[…]⚠ markers
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Hallucination Guard                    │
├───────────────┬───────────────┬───────────────┬──────────┤
│   CLI (Rich)  │   REST API    │  Python SDK   │          │
│   cli.py      │   FastAPI     │  detector.py  │          │
├───────────────┴───────┬───────┴───────────────┘          │
│                       │                                   │
│           ┌───────────▼───────────┐                      │
│           │    Detector Engine    │  app/detector.py      │
│           └──┬────────┬────────┬─┘                       │
│              │        │        │                          │
│     ┌────────▼─┐  ┌───▼────┐  ┌▼──────────┐             │
│     │  Claims  │  │ Verify │  │  Scorer   │             │
│     │  Extract │  │ Engine │  │           │             │
│     │  (spaCy) │  │ (Wiki  │  │  Risk     │             │
│     │          │  │ +SBERT)│  │  Compute  │             │
│     └──────────┘  └────────┘  └─────┬─────┘             │
│                                     │                    │
│                        ┌────────────▼────────────┐       │
│                        │   Highlight Engine      │       │
│                        │   (plain + Rich CLI)    │       │
│                        └─────────────────────────┘       │
└──────────────────────────────────────────────────────────┘
```

### Project Structure

```
.
├── app/
│   ├── __init__.py          # Package metadata
│   ├── main.py              # FastAPI REST API server
│   ├── detector.py          # Orchestration layer (SDK entry-point)
│   ├── claims.py            # Claim extraction engine (spaCy NLP)
│   ├── verifier.py          # Fact verification (Wikipedia + SBERT)
│   ├── scorer.py            # Hallucination risk scoring
│   ├── highlight.py         # Text highlighting (plain + Rich)
│   └── config.py            # Centralised settings (env vars)
├── tests/
│   ├── test_claims.py       # Claim extraction tests
│   ├── test_verifier.py     # Verification engine tests
│   ├── test_scorer.py       # Risk scoring tests
│   ├── test_highlight.py    # Highlighting tests
│   ├── test_detector.py     # Integration tests
│   ├── test_api.py          # FastAPI endpoint tests
│   └── sample_cases.json    # Sample hallucination test data
├── examples/
│   ├── basic_usage.py       # SDK usage examples
│   └── api_client.py        # REST API client example
├── docs/
│   └── ARCHITECTURE.md      # Detailed architecture docs
├── .github/
│   ├── workflows/
│   │   └── ci.yml           # CI pipeline (lint, test, Docker)
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md    # Bug report template
│       └── feature_request.md  # Feature request template
├── cli.py                   # CLI interface (Click + Rich)
├── pyproject.toml           # Packaging & tool config
├── requirements.txt         # Pinned dependencies
├── Dockerfile               # Production container
├── docker-compose.yml       # One-command deployment
├── Makefile                 # Dev task automation
├── CONTRIBUTING.md          # Contribution guide
├── LICENSE                  # MIT
└── README.md
```

---

## Configuration

All settings via environment variables or constructor arguments:

| Environment Variable | Default | Description |
| --- | --- | --- |
| `HALLUCINATION_GUARD_SPACY_MODEL` | `en_core_web_sm` | spaCy language model |
| `HALLUCINATION_GUARD_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `HALLUCINATION_GUARD_WIKI_LANG` | `en` | Wikipedia language edition |
| `HALLUCINATION_GUARD_SUPPORT_THRESHOLD` | `0.45` | Min similarity for supported |
| `HALLUCINATION_GUARD_HOST` | `0.0.0.0` | API bind address |
| `HALLUCINATION_GUARD_PORT` | `8000` | API port |
| `HALLUCINATION_GUARD_LOG_LEVEL` | `INFO` | Logging level |

---

## How It Works

1. **Claim Extraction** — spaCy NLP parses the input text. Sentences containing factual indicators (*is*, *founded*, *invented*, *born*, etc.) or named entities are extracted as structured claims with subject-verb-object triples.

2. **Fact Verification** — Each claim generates search queries against Wikipedia. Retrieved evidence passages are compared to the claim text using a sentence-transformer model (`all-MiniLM-L6-v2`), producing a cosine-similarity confidence score.

3. **Risk Scoring** — A weighted formula combines three signals:
   - **Unsupported ratio** (50%) — fraction of claims that failed verification
   - **Inverse confidence** (35%) — average `(1 − similarity)` across all claims
   - **Severity penalty** (15%) — non-linear bonus when >50% of claims fail

4. **Highlighting** — Unsupported claims are wrapped with `⚠[…]⚠` markers in the output text. The CLI renders these as **bold red** via Rich.

---

## Roadmap

- [ ] LLM-based claim extraction (GPT / local LLM fallback)
- [ ] Multi-source verification (Google Knowledge Graph, Wikidata, PubMed)
- [ ] Async pipeline for concurrent verification
- [ ] Caching layer (Redis / SQLite for Wikipedia + embeddings)
- [x] Docker image with one-command deployment
- [ ] Web UI dashboard
- [ ] Batch processing (multiple documents per call)
- [ ] Custom knowledge bases (plug in your own corpus)
- [x] CI/CD integration (GitHub Actions)
- [ ] PyPI package (`pip install hallucination-guard`)
- [ ] Webhook notifications for flagged content
- [ ] Confidence calibration with human-labeled datasets

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up the development environment
- Running tests and linting
- Submitting pull requests
- Code style expectations

### Quick Start for Contributors

```bash
git clone https://github.com/chumarjamil/hallucination-guard.git
cd hallucination-guard
make dev    # editable install + dev deps + pre-commit hooks
make test   # run full test suite
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built for developers who ship AI responsibly.</strong><br>
  <sub>If this project helps you, consider giving it a ⭐</sub>
</p>
