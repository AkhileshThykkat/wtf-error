"""Repository helpers for incident records stored in Cloudflare D1.

Uses the D1 Python Workers async binding API::

    db.prepare("SELECT ... WHERE id = ?").bind(incident_id).first()
    db.prepare("INSERT INTO ...").bind(...).run()
    db.prepare("SELECT ...").bind(...).all()  # ``run()`` is an alias

``db`` is the D1 database binding (e.g. ``env.DB`` or, inside FastAPI,
``request.scope["env"].DB``). All functions are async and return plain
Python dicts so results are JSON-serializable.
"""

from __future__ import annotations

from typing import Any, Mapping, TypeVar

_T = TypeVar("_T")

try:  # pragma: no cover - typing only, runtime uses duck-typing
    from schemas import IncidentCreate
except Exception:  # pragma: no cover - repo-root layout or broken schema
    try:
        from src.schemas import IncidentCreate  # type: ignore[no-redef]
    except Exception:
        IncidentCreate = Any  # type: ignore[no-redef,misc]

TABLE = "incidents"
COLUMNS = "id, title, symptoms, environment, created_at"
_RECORD_KEYS = ("id", "title", "symptoms", "environment", "created_at")


class RepositoryHelpers:
    """Internal D1 helpers grouped as static methods."""

    @staticmethod
    def _incident_fields(incident: Any) -> tuple[Any, Any, Any]:
        """Extract (title, symptoms, environment) from a model or mapping."""
        if isinstance(incident, Mapping):
            return incident["title"], incident["symptoms"], incident["environment"]
        if isinstance(incident, dict):  # pragma: no cover - Mapping covers this
            return incident["title"], incident["symptoms"], incident["environment"]
        # Pydantic model (IncidentCreate) or any object with attributes.
        if hasattr(incident, "model_dump"):
            try:
                data = incident.model_dump()
                if isinstance(data, dict):
                    return data["title"], data["symptoms"], data["environment"]
            except Exception:
                pass
        if isinstance(incident, (list, tuple)) and len(incident) == 3:
            return incident[0], incident[1], incident[2]
        return incident.title, incident.symptoms, incident.environment

    @staticmethod
    def _maybe_to_py(value: _T) -> _T:
        """Convert a Pyodide JsProxy to plain Python when possible."""
        if value is None:
            return value
        to_py = getattr(value, "to_py", None)
        if callable(to_py):
            try:
                converted: _T = to_py()
                return converted
            except Exception:
                return value
        return value

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any] | None:
        """Normalize a single D1 row (JS object, dict, or attribute object)."""
        if row is None:
            return None
        row = RepositoryHelpers._maybe_to_py(row)
        if row is None:
            return None
        if isinstance(row, dict):
            return dict(row)
        if isinstance(row, Mapping):
            return dict(row)

        # Attribute-style row (real D1 binding exposes columns as attributes,
        # e.g. ``row.id`` as in the fastapi-todo example).
        try:
            record: dict[str, Any] = {}
            found = False
            for key in _RECORD_KEYS:
                if hasattr(row, key):
                    record[key] = RepositoryHelpers._maybe_to_py(getattr(row, key))
                    found = True
                elif isinstance(row, (list, tuple)):
                    break
                else:
                    try:
                        record[key] = RepositoryHelpers._maybe_to_py(row[key])  # type: ignore[index]
                        found = True
                    except Exception:
                        continue
            if found:
                return record
        except Exception:
            pass

        # Fallbacks for mock objects.
        for attr in ("__dict__",):
            try:
                data = getattr(row, attr)
                if isinstance(data, dict) and data:
                    return {k: RepositoryHelpers._maybe_to_py(v) for k, v in data.items()}
            except Exception:
                continue
        try:
            return dict(row)
        except Exception:
            pass
        try:
            return dict(vars(row))
        except Exception:
            pass
        return None

    @staticmethod
    def _result_rows(result: Any) -> list[Any]:
        """Extract the row list from a D1Result (``run()``/``all()`` output)."""
        if result is None:
            return []
        results: Any = getattr(result, "results", None) if not isinstance(result, dict) else result.get("results")
        if results is None and isinstance(result, Mapping):
            results = result.get("results")
        if results is None and isinstance(result, (list, tuple)):
            return list(result)
        if results is None:
            converted = RepositoryHelpers._maybe_to_py(result)
            if isinstance(converted, dict) and "results" in converted:
                results = converted["results"]
            elif isinstance(converted, (list, tuple)):
                return list(converted)
            else:
                return []
        results = RepositoryHelpers._maybe_to_py(results)
        if results is None:
            return []
        if isinstance(results, (list, tuple)):
            return list(results)
        try:
            return list(results)
        except Exception:
            return []

    @staticmethod
    def _is_success(result: Any) -> bool:
        """Return False only when D1 explicitly reports failure."""
        try:
            if isinstance(result, dict):
                success = result.get("success", True)
            else:
                success = getattr(result, "success", True)
                if isinstance(success, dict):
                    success = True
            success = RepositoryHelpers._maybe_to_py(success)
            if isinstance(success, bool):
                return success
            if success is None:
                return True
            return bool(success)
        except Exception:
            return True

    @staticmethod
    def _coerce_row_id(value: object) -> int | str | None:
        """Narrow an arbitrary meta value to a usable row id."""
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return value if value != "" else None
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return None

    @staticmethod
    def _last_row_id(result: Any) -> int | str | None:
        """Extract ``meta.last_row_id`` from dict- or attribute-style results."""
        candidates: list[Any] = []
        try:
            if isinstance(result, dict):
                meta = result.get("meta")
                candidates.append(meta.get("last_row_id") if isinstance(meta, dict) else None)
                candidates.append(result.get("last_row_id"))
            else:
                meta = getattr(result, "meta", None)
                if meta is not None:
                    if isinstance(meta, dict):
                        candidates.append(meta.get("last_row_id"))
                    else:
                        candidates.append(getattr(meta, "last_row_id", None))
                        try:
                            candidates.append(meta["last_row_id"])  # type: ignore[index]
                        except Exception:
                            pass
                candidates.append(getattr(result, "last_row_id", None))
        except Exception:
            pass
        # Also try a to_py-converted payload.
        try:
            converted = RepositoryHelpers._maybe_to_py(result)
            if isinstance(converted, dict):
                meta_obj = converted.get("meta")
                if isinstance(meta_obj, dict):
                    coerced = RepositoryHelpers._coerce_row_id(meta_obj.get("last_row_id"))
                    if coerced is not None and coerced != 0:
                        return coerced
        except Exception:
            pass
        for value in candidates:
            coerced = RepositoryHelpers._coerce_row_id(RepositoryHelpers._maybe_to_py(value))
            if coerced is not None and coerced != 0:
                return coerced
        # ``0`` is D1's sentinel for non-inserts; report None when nothing real.
        return None

    @staticmethod
    async def _execute_run(bound_stmt: Any) -> Any:
        """Await ``run()`` (falling back to ``all()`` for minimal mocks)."""
        run = getattr(bound_stmt, "run", None)
        if callable(run):
            return await run()
        all_fn = getattr(bound_stmt, "all", None)
        if callable(all_fn):
            return await all_fn()
        raise AttributeError("D1 statement has neither run() nor all()")

    @staticmethod
    async def _fetch_all(bound_stmt: Any) -> Any:
        """Await ``all()`` (falling back to ``run()``, which D1 aliases)."""
        all_fn = getattr(bound_stmt, "all", None)
        if callable(all_fn):
            return await all_fn()
        run = getattr(bound_stmt, "run", None)
        if callable(run):
            return await run()
        raise AttributeError("D1 statement has neither all() nor run()")


async def create_incident(db: Any, incident: Any) -> dict[str, Any] | None:
    """Insert a complete incident record, then return it.

    The insert is awaited first; the freshly inserted row is read back
    (via ``meta.last_row_id``) only after the insert succeeds.
    """
    title, symptoms, environment = RepositoryHelpers._incident_fields(incident)

    insert_stmt = db.prepare(
        f"INSERT INTO {TABLE} (title, symptoms, environment) VALUES (?, ?, ?)"
    ).bind(title, symptoms, environment)
    insert_result = await RepositoryHelpers._execute_run(insert_stmt)

    if not RepositoryHelpers._is_success(insert_result):
        raise RuntimeError("Failed to insert incident")

    last_id = RepositoryHelpers._last_row_id(insert_result)
    if last_id is not None:
        row = (
            await db.prepare(
                f"SELECT {COLUMNS} FROM {TABLE} WHERE id = ? LIMIT 1"
            )
            .bind(last_id)
            .first()
        )
        record = RepositoryHelpers._row_to_dict(row)
        if record is not None:
            return record

    # Fallback when the binding does not surface last_row_id (e.g. some
    # mocks): return the most recently created row.
    row = (
        await db.prepare(
            f"SELECT {COLUMNS} FROM {TABLE} ORDER BY id DESC LIMIT 1"
        ).first()
    )
    return RepositoryHelpers._row_to_dict(row)


async def get_incident(db: Any, incident_id: Any) -> dict[str, Any] | None:
    """Return a single incident record, or None if absent."""
    row = (
        await db.prepare(f"SELECT {COLUMNS} FROM {TABLE} WHERE id = ? LIMIT 1")
        .bind(incident_id)
        .first()
    )
    return RepositoryHelpers._row_to_dict(row)


async def list_incidents(db: Any, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    """Return incidents ordered by created_at DESC, id DESC."""
    bound = db.prepare(
        f"SELECT {COLUMNS} FROM {TABLE} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    ).bind(limit, offset)
    result = await RepositoryHelpers._fetch_all(bound)
    records: list[dict[str, Any]] = []
    for row in RepositoryHelpers._result_rows(result):
        record = RepositoryHelpers._row_to_dict(row)
        if record is not None:
            records.append(record)
    return records
