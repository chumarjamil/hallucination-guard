<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/npm-package-red?style=for-the-badge&logo=npm&logoColor=white" alt="npm">
  <img src="https://img.shields.io/badge/typescript-ready-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/status-active-brightgreen?style=for-the-badge" alt="Status: Active">
</p>

<h1 align="center">🛡 Hallucination Guard</h1>

<p align="center">
  <strong>The open-source standard for detecting and preventing hallucinations in AI systems.</strong><br><br>
  CLI · SDK · API · Built for developers · Production-ready<br><br>
  <code>pip install hallucination-guard</code> · <code>npm install hallucination-guard</code>
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
| **Node.js / TS SDK**   | `npm install` — use from any JS/TS project         |
| **Cross-platform**     | Works on macOS, Linux, Windows                     |

---

## Quick Start

### Python

```bash
pip install hallucination-guard
python -m spacy download en_core_web_sm
```

### Node.js / TypeScript

```bash
npm install hallucination-guard
# or
yarn add hallucination-guard
# or
pnpm add hallucination-guard
```

> **Note:** The npm package requires the Python engine installed via `pip install hallucination-guard`.

### From Source

```bash
git clone https://github.com/chumarjamil/hallucination-guard.git
cd hallucination-guard
pip install -e .
python -m spacy download en_core_web_sm
```

### Try It — One Command

```bash
hallucination-guard check "The Eiffel Tower is located in Berlin."
```

### Try It — Python

```python
from hallucination_guard import detect

result = detect("The Eiffel Tower is located in Berlin.")
print(result.hallucinated)     # True
print(result.confidence)       # 0.91
print(result.explanation)      # "Detected 1 unsupported claim(s) …"
```

### Try It — TypeScript / JavaScript

```typescript
import { detect } from 'hallucination-guard';

const result = await detect("The Eiffel Tower is located in Berlin.");
console.log(result.hallucinated);       // true
console.log(result.confidence);         // 0.91
console.log(result.explanation);        // "Detected 1 unsupported claim(s) …"
```

---

## CLI

World-class developer CLI powered by Typer + Rich. Confidence bars, progress indicators, colored output.

### Commands

```bash
# Check inline text
hallucination-guard check "Paris is the capital of Germany."

# With per-claim explanations
hallucination-guard check "text" --explain

# JSON output
hallucination-guard check "text" --json

# Set risk threshold for PASS/FAIL
hallucination-guard check "text" --confidence-threshold 0.4

# Write output to file
hallucination-guard check "text" --output result.json

# Check a file
hallucination-guard file article.txt --pretty --explain

# Batch check with progress bar
hallucination-guard batch dataset.json --output results.json

# Benchmark against golden dataset
hallucination-guard benchmark tests/golden_dataset.json

# Start REST API server
hallucination-guard api --port 8000

# Debug mode
hallucination-guard check "text" --debug

# Quiet mode (result only)
hallucination-guard check "text" --quiet --json
```

### CLI Flags

| Flag                     | Short | Description                                 |
| ------------------------ | ----- | ------------------------------------------- |
| `--json`                 | `-j`  | Raw JSON output                             |
| `--pretty / --no-pretty` |       | Pretty-print (default: on)                  |
| `--explain`              | `-e`  | Show per-claim explanations                 |
| `--confidence-threshold` | `-t`  | Risk threshold for PASS/FAIL (default: 0.5) |
| `--output`               | `-o`  | Write JSON to file                          |
| `--debug`                |       | Debug logging                               |
| `--quiet`                | `-q`  | Suppress extra output                       |

### Sample Output

```
╭────────────────── 🛡  Hallucination Guard ──────────────────╮
│  ✗ 72% Hallucination Risk  [HIGH]                         │
╰────────────────────────────────────── 2.3s ────────╯
  Confidence  ██████░░░░░░░░░░░░░░ 28%
  Risk        ██████████████░░░░░░ 72%

  Total claims    2
  Supported       0
  Unsupported     2

─────────────── Highlighted Text ───────────────
  ⚠[The Eiffel Tower is located in Berlin …]⚠

──────────────── Flagged Claims ────────────────
  # │ Claim                      │ Confidence          │ Source
  1 │ The Eiffel Tower is in …   │ ████░░░░░░░░░░ 21% │ Wikipedia

╭─────────────────────────────────────────────────╮
│ ⚠  FAIL  Risk 72% exceeds threshold 50%      │
╰─────────────────────────────────────────────────╯
```

### Benchmark

```bash
hallucination-guard benchmark tests/golden_dataset.json
hallucination-guard benchmark dataset.json --json --output report.json
```

Outputs accuracy, precision, recall, F1 score, confusion matrix, and per-case details with progress bar.

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

## Node.js / TypeScript SDK

Same three functions, async-friendly:

### `detect(text)` — Full Pipeline

```typescript
import { detect } from 'hallucination-guard';

const result = await detect("Albert Einstein invented the telephone.");

console.log(result.hallucinated);       // true
console.log(result.hallucination_risk); // 0.68
console.log(result.flagged_claims);     // [{claim: "...", confidence: 0.12}]
console.log(result.highlighted_text);   // "⚠[Albert Einstein …]⚠"
```

### `score(text)` — Risk Score Only

```typescript
import { score } from 'hallucination-guard';

const risk = await score("The Great Wall was built by NASA.");
console.log(risk); // 0.72
```

### `explain(text)` — Structured Explanation

```typescript
import { explain } from 'hallucination-guard';

const info = await explain("Mars is the largest planet.");
console.log(info.hallucinated); // true
console.log(info.claims);       // [{claim: "...", severity: "high"}]
```

### API Mode (No CLI Needed)

If you prefer not to call the CLI subprocess, start the API server and use API mode:

```typescript
import { detect } from 'hallucination-guard';

const result = await detect("Some text", {
  mode: "api",
  apiUrl: "http://localhost:8000",
});
```

### Check Installation

```typescript
import { isInstalled } from 'hallucination-guard';

if (await isInstalled()) {
  console.log("Ready to use!");
} else {
  console.log("Run: pip install hallucination-guard");
}
```

---

## REST API

Production-grade FastAPI server with auth, rate limiting, batch processing, and metrics.

### Start the Server

```bash
hallucination-guard api --port 8000

# With API key authentication
HALLUCINATION_GUARD_API_KEY=your-secret-key hallucination-guard api

# Custom rate limit (requests/min per IP)
HALLUCINATION_GUARD_RATE_LIMIT=120 hallucination-guard api
```

### Endpoints

| Method | Path            | Description                                |
| ------ | --------------- | ------------------------------------------ |
| `GET`  | `/health`       | Health check + model status                |
| `GET`  | `/metrics`      | Server metrics (requests, latency, uptime) |
| `POST` | `/detect`       | Single text detection                      |
| `POST` | `/detect/batch` | Batch detection (multiple texts)           |
| `GET`  | `/docs`         | Interactive OpenAPI docs                   |
| `GET`  | `/redoc`        | ReDoc API reference                        |

### `POST /detect`

```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"text": "The Great Wall of China was built in 1995 by NASA."}'
```

### `POST /detect/batch`

```bash
curl -X POST http://localhost:8000/detect/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Text one.", "Text two.", "Text three."]}'
```

```json
{"results": [...], "total": 3, "processing_time_ms": 2340.5}
```

### `GET /metrics`

```json
{
  "total_requests": 142,
  "total_detections": 156,
  "total_batch_detections": 8,
  "avg_latency_ms": 1230.5,
  "total_claims_analysed": 412,
  "total_hallucinations_detected": 87,
  "uptime_seconds": 3600.0
}
```

---

## Integrations

First-class integration modules — import directly, no wrapper code needed.

| Integration    | Import                                                                             | Description                           |
| -------------- | ---------------------------------------------------------------------------------- | ------------------------------------- |
| **LangChain**  | `from hallucination_guard.integrations.langchain import HallucinationCallback`     | Callback handler for LLM chains       |
| **LlamaIndex** | `from hallucination_guard.integrations.llamaindex import HallucinationGuardPlugin` | Query pipeline plugin                 |
| **RAG**        | `from hallucination_guard.integrations.rag import RAGGuard, rag_verify`            | Wrapper + decorator for RAG functions |

### LangChain Callback

```python
from hallucination_guard.integrations.langchain import HallucinationCallback

callback = HallucinationCallback(threshold=0.5)

# Use with any LangChain LLM
llm = ChatOpenAI(callbacks=[callback])
response = llm.invoke("Tell me about the Eiffel Tower")

# Check results
print(callback.flagged)       # True/False
print(callback.last_result)   # Full DetectionResult
print(callback.history)       # All checks
```

### LlamaIndex Plugin

```python
from hallucination_guard.integrations.llamaindex import HallucinationGuardPlugin

plugin = HallucinationGuardPlugin(threshold=0.5)

response = query_engine.query("What is Python?")
result = plugin.verify_response(response)

print(result["safe"])   # True/False
print(result["risk"])   # 0.0–1.0
print(plugin.get_stats())  # Aggregate stats
```

### RAG Guard (Wrapper + Decorator)

```python
from hallucination_guard.integrations.rag import RAGGuard, rag_verify

# Wrapper class
guard = RAGGuard(my_rag_fn, threshold=0.4)
result = guard.query("What is Python?")
print(result.safe, result.risk)

# Decorator — raises HallucinationError if threshold exceeded
@rag_verify(threshold=0.4)
def my_rag(query: str) -> str:
    return "some answer"

result = my_rag("What is Python?")
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
│   ├── cli.py                 # Typer CLI (check, file, batch, benchmark, api)
│   ├── core/
│   │   ├── detector.py        # Pipeline orchestration
│   │   ├── claims.py          # Claim extraction (spaCy)
│   │   ├── verifier.py        # Fact verification (Wikipedia + SBERT)
│   │   ├── scorer.py          # Risk scoring engine
│   │   ├── explainer.py       # Explanation generation
│   │   └── highlight.py       # Text highlighting
│   ├── integrations/
│   │   ├── langchain.py       # LangChain callback handler
│   │   ├── llamaindex.py      # LlamaIndex plugin
│   │   └── rag.py             # RAG guard + decorator
│   ├── api/
│   │   └── server.py          # FastAPI REST server (auth, batch, metrics)
│   └── utils/
│       └── config.py          # Env-based configuration
├── npm/                       # Node.js / TypeScript SDK
│   ├── src/index.ts           # JS/TS client library
│   ├── bin/cli.js             # npx CLI wrapper
│   └── package.json
├── tests/                     # Unit + integration tests
├── examples/                  # Integration examples
├── docs/                      # Architecture documentation
├── pyproject.toml             # Python package config
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
| `HALLUCINATION_GUARD_API_KEY`           | *(disabled)*       | API key for auth (optional)    |
| `HALLUCINATION_GUARD_RATE_LIMIT`        | `60`               | Max requests/min per IP        |

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
```

---

## Roadmap

- [x] Claim extraction + fact verification pipeline
- [x] CLI with Rich output
- [x] REST API (FastAPI)
- [x] Python SDK (`detect`, `score`, `explain`)
- [x] Explanation engine with severity ratings
- [x] Node.js / TypeScript SDK (npm package)
- [x] First-class integrations (LangChain, LlamaIndex, RAG)
- [x] Benchmark system with precision/recall/F1
- [x] API key authentication + rate limiting
- [x] Batch processing API endpoint
- [x] Metrics endpoint (`/metrics`)
- [x] CI/CD (GitHub Actions)
- [x] Issue/PR templates + security policy
- [ ] LLM-based claim extraction (GPT / Ollama / local)
- [ ] Multi-source verification (Wikidata, PubMed, Knowledge Graph)
- [ ] Async pipeline for concurrent verification
- [ ] Caching layer (Redis / SQLite)
- [ ] Custom knowledge bases
- [ ] Web UI dashboard
- [ ] PyPI + npm package distribution
- [ ] OpenTelemetry observability
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
