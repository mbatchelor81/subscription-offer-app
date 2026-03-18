We’re building a TMT “Subscriber Offer Decisioning” application that demonstrates how a telecom can personalize retention and upsell offers in real time.

Business behavior:
1) A user (sales/marketing analyst) can enter a few subscriber attributes:
   - subscriber id
   - tenure (months)
   - average monthly spend
   - churn risk score (0 to 1)
   - current plan
2) The system returns:
   - a recommended offer (a named offer)
   - a discount percentage (if applicable)
   - a clear, customer-friendly explanation (“why this offer”)

Constraints:
- The recommendation itself must be deterministic and explainable (no “random AI decisions”).
- The explanation can be enhanced by AI, but the offer/discount decision must not change based on AI.
- This must run locally with docker compose and be demoable in < 2 minutes.

Acceptance criteria:
- There is a simple web page where I can input the fields and see the output immediately.
- There is a simple API powering it (so we can later productionize it).

Technical Implementation Notes:
- CORS must be configured in the backend to allow frontend (localhost:3000) to access backend API (localhost:8000)
- Add CORS middleware with allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] for local development

Please implement this into the existing monorepo scaffold:
- Backend in @services/offer-decision-service 
- UI in @web/demo-ui 