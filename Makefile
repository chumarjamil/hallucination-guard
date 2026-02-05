.PHONY: install dev test lint typecheck format serve demo clean

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install:
	pip install -r requirements.txt
	pip install -e .
	python -m spacy download en_core_web_sm

dev:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm
	pre-commit install || true

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

test:
	pytest tests/ -v --tb=short --cov=src/hallucination_guard --cov-report=term-missing

lint:
	ruff check src/ tests/

typecheck:
	mypy src/ --ignore-missing-imports

format:
	ruff format src/ tests/

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

serve:
	hallucination-guard api --port 8000 --reload

demo:
	hallucination-guard check "The Eiffel Tower is located in Berlin and was built in 1920."

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build
