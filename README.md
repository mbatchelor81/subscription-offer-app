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

- Docker & Docker Compose (for remote testing)
- Python 3.12 & Node 20 (for local development)

## Local Development

For local development and testing, use the direct startup commands:

```bash
# Terminal 1 - Backend
cd services/offer-decision-service
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd web/demo-ui
nvm use 18
npm run dev
```

The backend is available at **http://localhost:8000** and the frontend at **http://localhost:3000**.

## Docker (Remote Testing)

For containerized deployment and remote testing:

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

## Demo Scenarios

The UI includes 3 pre-configured scenarios for quick demos:

1. **High Value Customer** - Shows premium upgrade (15% discount)
2. **At Risk Customer** - Shows retention offer (25% discount)  
3. **New Customer** - Shows basic value offer (5% discount)

## Health Check

```bash
curl http://localhost:8000/healthz
```
