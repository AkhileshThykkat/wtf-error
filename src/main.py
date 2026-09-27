from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from workers import asgi

from evidence import prepare_evidence, redact_secrets
from investigation import (
    IncidentNotFoundError,
    WorkersAIRequestError,
    investigate_incident,
)
from repository import (
    create_evidence,
    create_incident as create_incident_in_db,
    create_message,
    get_incident as get_incident_from_db,
    list_evidence,
    list_findings,
    list_incidents as list_incidents_from_db,
    list_messages,
)
from schemas import EvidenceCreate, IncidentCreate, IncidentResponse, MessageCreate

app = FastAPI(title="wtf-error")


def _db(request: Request) -> Any:
    return request.scope["env"].DB


async def _require_incident(db: Any, incident_id: str) -> dict[str, Any]:
    incident = await get_incident_from_db(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "wtf-error"}


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate, request: Request
) -> dict[str, Any]:
    db = _db(request)
    now = datetime.now(timezone.utc).isoformat()
    incident: dict[str, Any] = {
        "id": str(uuid4()),
        "title": redact_secrets(payload.title),
        "symptoms": redact_secrets(payload.symptoms),
        "environment": redact_secrets(payload.environment),
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }
    return await create_incident_in_db(db, incident)


@app.get("/api/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    return await list_incidents_from_db(_db(request), limit, offset)


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, request: Request) -> dict[str, Any]:
    return await _require_incident(_db(request), incident_id)


@app.get("/api/incidents/{incident_id}/evidence")
async def get_evidence(incident_id: str, request: Request) -> list[dict[str, Any]]:
    db = _db(request)
    await _require_incident(db, incident_id)
    return await list_evidence(db, incident_id)


@app.post("/api/incidents/{incident_id}/evidence", status_code=201)
async def add_evidence(
    incident_id: str, payload: EvidenceCreate, request: Request
) -> dict[str, Any]:
    db = _db(request)
    await _require_incident(db, incident_id)
    evidence_id = f"EV-{uuid4().hex[:12].upper()}"
    processed, _ = prepare_evidence(payload.content, evidence_id)
    return await create_evidence(
        db,
        {
            "id": evidence_id,
            "incident_id": incident_id,
            "source": redact_secrets(payload.source),
            "content": processed,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/api/incidents/{incident_id}/messages")
async def get_messages(incident_id: str, request: Request) -> list[dict[str, Any]]:
    db = _db(request)
    await _require_incident(db, incident_id)
    return await list_messages(db, incident_id)


@app.post("/api/incidents/{incident_id}/messages", status_code=201)
async def add_message(
    incident_id: str, payload: MessageCreate, request: Request
) -> dict[str, Any]:
    db = _db(request)
    await _require_incident(db, incident_id)
    now = datetime.now(timezone.utc).isoformat()
    return await create_message(
        db,
        {
            "id": str(uuid4()),
            "incident_id": incident_id,
            "role": "user",
            "content": redact_secrets(payload.content),
            "created_at": now,
            "updated_at": now,
        },
    )


@app.get("/api/incidents/{incident_id}/findings")
async def get_findings(incident_id: str, request: Request) -> list[dict[str, Any]]:
    db = _db(request)
    await _require_incident(db, incident_id)
    return await list_findings(db, incident_id)


@app.post("/api/incidents/{incident_id}/investigate")
async def investigate(incident_id: str, request: Request) -> dict[str, Any]:
    db = _db(request)
    await _require_incident(db, incident_id)
    try:
        return await investigate_incident(db, request.scope["env"].AI, incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Incident not found") from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail="Workers AI returned an invalid investigation"
        ) from exc
    except WorkersAIRequestError as exc:
        raise HTTPException(status_code=502, detail="Workers AI request failed") from exc


Default = asgi.entrypoint(app)
