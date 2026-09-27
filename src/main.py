from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from workers import asgi

from repository import (
    create_incident as create_incident_in_db,
)
from repository import (
    get_incident as get_incident_from_db,
)
from repository import (
    list_incidents as list_incidents_from_db,
)
from schemas import IncidentCreate, IncidentResponse

app = FastAPI(title="wtf-error")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "wtf-error"}


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate, request: Request
) -> dict[str, Any]:
    db: Any = request.scope["env"].DB
    now: str = datetime.now(timezone.utc).isoformat()
    incident: dict[str, Any] = {
        "id": str(uuid4()),
        "title": payload.title,
        "symptoms": payload.symptoms,
        "environment": payload.environment,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }
    saved: dict[str, Any] = await create_incident_in_db(db, incident)
    return saved


@app.get("/api/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    db: Any = request.scope["env"].DB
    return await list_incidents_from_db(db, limit, offset)


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, request: Request) -> dict[str, Any]:
    db: Any = request.scope["env"].DB
    incident: dict[str, Any] | None = await get_incident_from_db(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


Default = asgi.entrypoint(app)
