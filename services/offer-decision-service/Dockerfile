# =============================================================================
# offer-decision-service  —  Production Dockerfile (multi-stage)
# =============================================================================
# Runtime environment variables:
#   APP_ENV          – deployment environment (e.g. local, staging, production)
#   LOG_LEVEL        – Python log level (default: info)
#   OPENAI_API_KEY   – OpenAI API key for AI-enhanced explanations
#   OTEL_EXPORTER_OTLP_ENDPOINT – (optional) OpenTelemetry collector endpoint
# =============================================================================

# ---------- Stage 1: build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# ---------- Stage 2: production ----------
FROM python:3.12-slim AS production

LABEL maintainer="subscription-offer-app"

# Create a non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/

# Own the workdir
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
