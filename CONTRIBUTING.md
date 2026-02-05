# Contributing to Hallucination Guard

Thank you for your interest in contributing! This guide will help you get started.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Make (optional but recommended)

### Getting Started

```bash
# Fork and clone the repository
git clone https://github.com/<your-username>/hallucination-guard.git
cd hallucination-guard

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

# Install in development mode (editable + dev extras)
make dev

# Or manually:
pip install -e ".[dev]"
python -m spacy download en_core_web_sm

# Verify the CLI works
hallucination-guard version
```

---

## Running Tests

```bash
# Full test suite with coverage
make test

# Or manually:
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
```

All new features **must** include tests. All tests **must** pass before submitting a PR.

---

## Code Quality

### Linting

```bash
make lint       # check for issues
make format     # auto-fix formatting
```

### Type Checking

```bash
make typecheck
```

### Pre-commit Hooks

Pre-commit hooks are installed automatically with `make dev`. They run `ruff` and `mypy` on every commit.

To run them manually:

```bash
pre-commit run --all-files
```

---

## Pull Request Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** — keep commits focused and atomic
4. **Write or update tests** for any new functionality
5. **Run the full check suite**:
   ```bash
   make lint
   make typecheck
   make test
   ```
6. **Push** your branch and open a Pull Request against `main`
7. **Describe your changes** clearly in the PR description

### PR Requirements

- All CI checks must pass
- Tests must cover new functionality
- Code must follow the project style guide
- PR description must explain *what* and *why*

---

## Code Style

- **Python 3.10+** — use modern syntax (`match`, `|` union types where appropriate)
- **Type hints** on all public functions and methods
- **Logging** over `print` — use the `logging` module
- **Docstrings** on all public classes and functions (Google style)
- **Imports** — sorted by `ruff` (stdlib → third-party → local)
- **Line length** — 100 characters max
- **Naming** — `snake_case` for functions/variables, `PascalCase` for classes

---

## Project Structure

```
src/hallucination_guard/
  __init__.py    # Public API (detect, score, explain)
  sdk.py         # SDK convenience functions
  cli.py         # Typer CLI (check, file, batch, api)
  core/
    detector.py  # Pipeline orchestration
    claims.py    # Claim extraction (spaCy)
    verifier.py  # Fact verification (Wikipedia + SBERT)
    scorer.py    # Risk scoring
    explainer.py # Explanation generation
    highlight.py # Text highlighting
  api/
    server.py    # FastAPI REST server
  utils/
    config.py    # Env-based configuration

tests/           # Test suite
examples/        # Integration examples
docs/            # Architecture documentation
```

### Where to Add Code

| Type of change          | Where                                       |
| ----------------------- | ------------------------------------------- |
| New verification source | `src/hallucination_guard/core/verifier.py`  |
| New scoring method      | `src/hallucination_guard/core/scorer.py`    |
| New explanation logic   | `src/hallucination_guard/core/explainer.py` |
| New API endpoint        | `src/hallucination_guard/api/server.py`     |
| New CLI command         | `src/hallucination_guard/cli.py`            |
| New SDK function        | `src/hallucination_guard/sdk.py`            |
| Configuration option    | `src/hallucination_guard/utils/config.py`   |

---

## Reporting Bugs

Use the [Bug Report](https://github.com/chumarjamil/hallucination-guard/issues/new?template=bug_report.md) issue template. Include:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Full error traceback

## Requesting Features

Use the [Feature Request](https://github.com/chumarjamil/hallucination-guard/issues/new?template=feature_request.md) issue template. Include:

- Problem description
- Proposed solution
- Why it matters

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
