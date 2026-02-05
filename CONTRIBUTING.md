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

# Install in development mode with all dev dependencies
make dev

# Or manually:
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
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
app/             # Core library code
  claims.py      # Claim extraction engine
  verifier.py    # Fact verification engine
  scorer.py      # Risk scoring
  highlight.py   # Text highlighting
  detector.py    # Orchestration (SDK entry-point)
  main.py        # FastAPI server
  config.py      # Configuration / settings

tests/           # Test suite
examples/        # Usage examples
docs/            # Documentation
cli.py           # CLI entry-point
```

### Where to Add Code

| Type of change | Where |
| --- | --- |
| New verification source | `app/verifier.py` |
| New scoring method | `app/scorer.py` |
| New API endpoint | `app/main.py` |
| New CLI command/option | `cli.py` |
| Configuration option | `app/config.py` |

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
