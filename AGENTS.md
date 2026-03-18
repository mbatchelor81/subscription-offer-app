## What this project is
A small TMT demo application that simulates a **Subscriber Offer Decisioning** capability for a telecom/media provider.

Core business functionality:
- Take a few subscriber attributes (tenure, spend, churn risk, current plan)
- Return a recommended offer + discount (if any)
- Return a clear explanation for why that offer was chosen
- The offer decision is **policy-driven and deterministic**; AI may only improve the wording of the explanation.

- **Backend:** Python 3.12 / FastAPI, served via Uvicorn.
- **Frontend:** Node 20 / React (Next.js dev server).

## How an agent should think about changes
- Preserve the business policy and output contract; do not change offer logic unless explicitly asked.
- Optimize for a smooth demo: “run locally in minutes, input → output works end-to-end.”
- Prefer small, reviewable PRs with clear summaries.
- For production hardening tasks, add guardrails (tests, CI checks, security gates) rather than bypassing them.
- Treat AI as an *augmentation layer* (explanation text), never as the decision-maker.

## Running the Demo Application
When asked to start the demo app, always use the skill in `.devin/skills/demo-quick-start/SKILL.md` which provides:
- Local development commands for backend and frontend
- Health check and demo test commands  
- Pre-configured demo scenarios for quick demonstrations
- Troubleshooting tips for common issues

The skill should be invoked first before attempting manual startup procedures.