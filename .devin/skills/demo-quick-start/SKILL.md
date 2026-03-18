---
name: demo-quick-start
description: Quick commands for running the Subscriber Offer Decisioning demo locally
allowed-tools:
  - read
  - exec
---

# Demo Quick Start Commands

Provides quick commands for running the Subscriber Offer Decisioning demo locally.

## Commands

### ⚡ Local Development Start
```bash
# Terminal 1 - Backend
cd services/offer-decision-service
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd web/demo-ui
source ~/.nvm/nvm.sh && nvm use 20
npm run dev
```

### 🎯 Demo Test Commands
```bash
# Health check
curl http://localhost:8000/healthz

### 🛑 Stop Services
```bash
# Stop local processes (Ctrl+C in terminals)
```

## Demo Scenarios

The UI includes 3 pre-configured scenarios for quick demos:

1. **High Value Customer** - Shows premium upgrade (15% discount)
2. **At Risk Customer** - Shows retention offer (25% discount)  
3. **New Customer** - Shows basic value offer (5% discount)

## Tips for Live Demos

- Use local development for faster iteration and debugging
- Click scenario buttons to instantly load demo data
- Each scenario demonstrates different business logic paths
- Results show deterministic offer decisions with clear explanations
- Access points: Frontend (http://localhost:3000), Backend (http://localhost:8000)

## Troubleshooting

If you get "Failed to get offer" error:
- Ensure both services are running
- Check that backend has CORS configured (already implemented)
- Verify ports 3000 and 8000 are available