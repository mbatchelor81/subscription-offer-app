# subscriber-offer-decisioning

Subscriber Offer Personalization Service — a working, demoable application slice
with a clean API contract, a minimal UI, and a basic test suite.

## Project Structure

```
services/offer-decision-service/   FastAPI backend
web/demo-ui/                       Next.js frontend
helm/offer-decision-service/       Helm chart (placeholder)
infra/terraform/                   Terraform modules (placeholder)
.github/workflows/                 CI/CD (placeholder)
```

## Prerequisites

- Docker & Docker Compose

## Local Development

```bash
# Copy env file
cp .env.example .env

# Start all services
make up

# Run backend tests
make test

# Format code
make fmt

# Lint code
make lint
```

The backend is available at **http://localhost:8000** and the frontend at **http://localhost:3000**.

## Health Check

```bash
curl http://localhost:8000/healthz
```
