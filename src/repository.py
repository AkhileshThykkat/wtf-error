"""Repository helpers for incident records stored in Cloudflare D1.

Uses the D1 Python Workers async binding API (see
https://developers.cloudflare.com/d1/worker-api/prepared-statements and
https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers):

    await db.prepare("INSERT INTO ...").bind(...).run()
    await db.prepare("SELECT ... WHERE id = ?").bind(...).first()
    await db.prepare("SELECT ...").bind(...).all()

``db`` is the D1 database binding (e.g. ``env.DB`` or, inside FastAPI,
``request.scope["env"].DB``).

Per the Python Workers FFI, D1 rows come back as JavaScript objects
proxied into Python, so columns are read via attribute access
(``row.id``, ``row.title``, ...) as in the official
``fastapi-todo`` / ``query-d1`` examples. ``all()`` returns a
``D1Result`` whose ``results`` attribute is the list of rows, and
``first()`` returns a single row object or ``None`` when no row matches.
Results are converted here into plain Python ``dict`` / ``list`` objects
so they are JSON-serializable.

All queries use parameterized SQL (``?`` placeholders + ``bind()``).
Errors are never swallowed: if D1 fails or conversion fails the
exception propagates to the caller.
"""

from __future__ import annotations

from typing import Any

COLUMNS = "id, title, symptoms, environment, status, created_at, updated_at"


async def create_incident(db: Any, incident: dict[str, Any]) -> dict[str, Any]:
    """Insert a complete incident record and return it.

    ``incident`` is already a complete dictionary containing all 7 fields
    (``id``, ``title``, ``symptoms``, ``environment``, ``status``,
    ``created_at``, ``updated_at``). The caller provides the ID, status,
    and timestamps -- nothing is generated here.
    """
    await (
        db.prepare(
            "INSERT INTO incidents "
            "(id, title, symptoms, environment, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        )
        .bind(
            incident["id"],
            incident["title"],
            incident["symptoms"],
            incident["environment"],
            incident["status"],
            incident["created_at"],
            incident["updated_at"],
        )
        .run()
    )
    return dict(incident)


async def get_incident(db: Any, incident_id: str) -> dict[str, Any] | None:
    """Return a single incident as a plain dict, or None if absent."""
    row = (
        await db.prepare(
            f"SELECT {COLUMNS} FROM incidents WHERE id = ? LIMIT 1"
        )
        .bind(incident_id)
        .first()
    )
    if row is None:
        return None
    return {
        "id": row.id,
        "title": row.title,
        "symptoms": row.symptoms,
        "environment": row.environment,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def list_incidents(
    db: Any, limit: int = 20, offset: int = 0
) -> list[dict[str, Any]]:
    """Return incidents ordered by created_at DESC, id DESC."""
    result = (
        await db.prepare(
            f"SELECT {COLUMNS} FROM incidents "
            "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
        )
        .bind(limit, offset)
        .all()
    )
    return [
        {
            "id": row.id,
            "title": row.title,
            "symptoms": row.symptoms,
            "environment": row.environment,
            "status": row.status,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in result.results
    ]
