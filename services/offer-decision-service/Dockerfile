# ============================================================
# offer-decision-service  —  multi-stage production Dockerfile
# ============================================================
# Runtime environment variables (set via ConfigMap / .env):
#   APP_ENV          – environment name (local | staging | production)
#   LOG_LEVEL        – Python log level (debug | info | warning | error)
#   OPENAI_API_KEY   – OpenAI API key for AI explanation enhancement
#   OTEL_EXPORTER_OTLP_ENDPOINT – (optional) OpenTelemetry collector URL
# ============================================================

# ---------- Stage 1: build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .

# Install production dependencies only into a virtual-env so we can
# copy just the site-packages to the runtime stage.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir .

# ---------- Stage 2: production ----------
FROM python:3.12-slim AS production

LABEL maintainer="offer-decision-service"

# Create a non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy only the virtual-env from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY app/ ./app/

# Ensure the venv binaries are on PATH
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check against the /healthz endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]

# Production CMD — no --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------- Stage 3: dev (used by docker-compose for local development) ----------
FROM production AS dev

USER root

# Need pyproject.toml for dev extras install
COPY pyproject.toml .

# Install dev dependencies (pytest, ruff, httpx) into the existing venv
RUN /opt/venv/bin/pip install --no-cache-dir ".[dev]"

# Copy test files
COPY tests/ ./tests/

# Create writable cache directories for dev tools
RUN mkdir -p /app/.pytest_cache /app/.ruff_cache \
    && chown -R appuser:appuser /app/.pytest_cache /app/.ruff_cache /app/tests

USER appuser

# Dev CMD — with --reload for hot-reloading
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
