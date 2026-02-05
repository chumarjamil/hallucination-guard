FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (for caching)
COPY requirements.txt pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir -e . && \
    python -m spacy download en_core_web_sm

# Pre-download sentence-transformer model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy remaining project files
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["hallucination-guard", "api", "--host", "0.0.0.0", "--port", "8000"]
