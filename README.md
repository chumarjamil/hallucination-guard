# 🛡 Hallucination Guard

**Production-ready AI Hallucination Detection for Developers**

Detect, score, and highlight hallucinations in AI-generated text — via Python SDK, CLI, or REST API.

---

## Why It Matters

Large Language Models frequently generate plausible-sounding but factually incorrect statements. **Hallucination Guard** gives developers a programmatic way to:

- **Extract** factual claims from any AI-generated text
- **Verify** each claim against trusted sources (Wikipedia + semantic similarity)
- **Score** the overall hallucination risk (`0.0` – `1.0`)
- **Highlight** problematic phrases for human review

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Hallucination Guard                 │
├─────────────┬──────────────┬────────────┬───────────┤
│  CLI (Rich) │  REST API    │ Python SDK │           │
│  cli.py     │  FastAPI     │ detector   │           │
├─────────────┴──────┬───────┴────────────┘           │
│                    │                                 │
│         ┌──────────▼──────────┐                     │
│         │   Detector Engine   │  (app/detector.py)  │
│         └──┬─────┬───────┬───┘                      │
│            │     │       │                           │
│   ┌────────▼┐ ┌──▼────┐ ┌▼────────┐                │
│   │ Claims  │ │Verify │ │ Scorer  │                 │
│   │ Extract │ │Engine │ │         │                 │
│   │ (spaCy) │ │(Wiki+ │ │ Risk    │                 │
│   │         │ │ SBERT)│ │ Compute │                 │
│   └─────────┘ └───────┘ └────┬────┘                │
│                               │                     │
│                    ┌──────────▼──────────┐          │
│                    │   Highlight Engine  │          │
│                    │  (plain + Rich CLI) │          │
│                    └────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### File Structure

```
hallucination-guard/
├── app/
│   ├── __init__.py        # Package metadata
│   ├── main.py            # FastAPI server
│   ├── detector.py        # Orchestration layer (Python SDK)
│   ├── claims.py          # Claim extraction (spaCy NLP)
│   ├── verifier.py        # Fact verification (Wikipedia + SBERT)
│   ├── scorer.py          # Risk scoring engine
│   ├── highlight.py       # Text highlighting (plain + Rich)
│   └── config.py          # Centralised settings (env vars)
├── tests/
│   ├── test_claims.py     # Claim extraction tests
│   ├── test_verifier.py   # Verification engine tests
│   ├── test_scorer.py     # Risk scoring tests
│   ├── test_highlight.py  # Highlighting tests
│   ├── test_detector.py   # Integration / orchestration tests
│   └── test_api.py        # FastAPI endpoint tests
├── examples/
│   ├── basic_usage.py     # SDK usage examples
│   └── api_client.py      # REST API client example
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions CI (lint, test, Docker)
├── cli.py                 # CLI interface (Click + Rich)
├── pyproject.toml         # Packaging, linting, testing config
├── requirements.txt       # Pinned dependencies
├── Dockerfile             # Production container image
├── docker-compose.yml     # One-command deployment
├── Makefile               # Common dev tasks
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE                # MIT
└── README.md
```

---

## Installation

### Quick Start

```bash
git clone https://github.com/your-org/hallucination-guard.git
cd hallucination-guard
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
make install                # installs deps + spaCy model
```

### Manual

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Development

```bash
make dev   # installs in editable mode with dev extras
```

### Docker

```bash
docker compose up -d        # build + run on port 8000
curl http://localhost:8000/health
```

---

## Usage

### 1. CLI Tool

```bash
# Direct text input
python cli.py "The Eiffel Tower is located in Berlin and was built in 1920."

# From a file
python cli.py --file article.txt

# Pipe from stdin
echo "Python was created by Guido van Rossum in 1991." | python cli.py

# Verbose mode
python cli.py -v "Some AI-generated text here."
```

**Sample CLI Output:**

```
╭──────────── Hallucination Guard ────────────╮
│     Hallucination Risk: 65.00%              │
╰──────────── confidence 35.00% ──────────────╯
  Total claims   : 2
  Supported      : 1
  Unsupported    : 1
  Avg similarity : 0.3200

Highlighted Text
The ⚠[Eiffel Tower is located in Berlin and was built in 1920.]⚠

┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Claim                          ┃ Confidence ┃ Evidence         ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ 1  │ The Eiffel Tower is located …  │ 0.2100     │ The Eiffel Tower │
│    │                                │            │ is a wrought-…   │
└────┴────────────────────────────────┴────────────┴──────────────────┘
```

### 2. REST API

Start the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{ "status": "ok", "version": "0.1.0" }
```

#### `POST /detect`

```bash
curl -X POST http://localhost:8000/detect \
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

### 3. Python SDK

```python
from app.detector import HallucinationDetector

detector = HallucinationDetector()

result = detector.detect(
    "Albert Einstein invented the telephone in 1876."
)

print(f"Risk:  {result.hallucination_risk}")
print(f"Flagged claims: {len(result.flagged_claims)}")

for fc in result.flagged_claims:
    print(f"  - {fc['claim']}  (confidence: {fc['confidence']})")
```

---

## Configuration

All settings can be passed programmatically **or** via environment variables:

| Env Variable                            | Default            | Description                                 |
| --------------------------------------- | ------------------ | ------------------------------------------- |
| `HALLUCINATION_GUARD_SPACY_MODEL`       | `en_core_web_sm`   | spaCy language model                        |
| `HALLUCINATION_GUARD_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model                  |
| `HALLUCINATION_GUARD_WIKI_LANG`         | `en`               | Wikipedia language edition                  |
| `HALLUCINATION_GUARD_SUPPORT_THRESHOLD` | `0.45`             | Min similarity to mark a claim as supported |
| `HALLUCINATION_GUARD_HOST`              | `0.0.0.0`          | API server bind address                     |
| `HALLUCINATION_GUARD_PORT`              | `8000`             | API server port                             |
| `HALLUCINATION_GUARD_LOG_LEVEL`         | `INFO`             | Logging level                               |

Or pass directly to the constructor:

```python
detector = HallucinationDetector(
    spacy_model="en_core_web_lg",
    transformer_model="all-mpnet-base-v2",
    wiki_lang="en",
)
```

---

## How It Works

1. **Claim Extraction** — spaCy NLP parses the text, identifies sentences with factual indicators (verbs like *is*, *founded*, *invented*) or named entities, and extracts structured claims.

2. **Fact Verification** — Each claim is queried against Wikipedia. The retrieved evidence is compared to the claim using a sentence-transformer model (`all-MiniLM-L6-v2`) that produces a cosine-similarity confidence score.

3. **Risk Scoring** — A weighted formula combines the unsupported-claim ratio, inverse confidence, and a non-linear severity penalty into a single `0.0 – 1.0` hallucination risk score.

4. **Highlighting** — Unsupported claims are marked in the original text: plain-text markers (`⚠[…]⚠`) for machine consumption, and **bold red** via Rich for CLI output.

---

## Roadmap

- [ ] **LLM-based claim extraction** — GPT / local LLM fallback for complex sentences
- [ ] **Multi-source verification** — Google Knowledge Graph, Wikidata, PubMed
- [ ] **Async pipeline** — concurrent verification for faster throughput
- [ ] **Caching layer** — Redis / SQLite cache for Wikipedia + embeddings
- [x] **Docker image** — one-command deployment
- [ ] **Web UI dashboard** — browser-based analysis interface
- [ ] **Batch processing** — analyse multiple documents in one call
- [ ] **Custom knowledge bases** — plug in your own ground-truth corpus
- [x] **CI / CD integration** — GitHub Action for automated content checks
- [ ] **PyPI package** — `pip install hallucination-guard`

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request with a clear description

### Development Setup

```bash
git clone https://github.com/your-org/hallucination-guard.git
cd hallucination-guard
make dev            # editable install + dev dependencies + pre-commit
```

### Useful Commands

```bash
make test           # run test suite with coverage
make lint           # ruff linter
make typecheck      # mypy type checking
make format         # auto-format code
make serve          # start dev server with hot-reload
make docker         # build Docker image
make clean          # remove caches and build artifacts
```

### Code Style

- Python 3.10+
- Type hints on all public functions
- `logging` over `print`
- Keep modules focused and testable
- Pre-commit hooks enforced via `ruff` + `mypy`

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for developers who care about factual accuracy.
</p>
