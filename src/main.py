from fastapi import FastAPI
from workers import asgi

app = FastAPI(title="wtf-error")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "wtf-error"}


Default = asgi.entrypoint(app)
