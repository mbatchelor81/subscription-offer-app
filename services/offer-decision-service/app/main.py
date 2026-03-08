from fastapi import FastAPI

app = FastAPI(title="Offer Decision Service", version="0.1.0")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
