.PHONY: install dev test lint typecheck format serve docker clean

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

dev:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm
	pre-commit install || true

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

test:
	pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

lint:
	ruff check app/ tests/ cli.py

typecheck:
	mypy app/ --ignore-missing-imports

format:
	ruff format app/ tests/ cli.py

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

serve:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cli:
	python cli.py "The Eiffel Tower is located in Berlin and was built in 1920."

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker:
	docker build -t hallucination-guard .

docker-run:
	docker compose up -d

docker-stop:
	docker compose down

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build
