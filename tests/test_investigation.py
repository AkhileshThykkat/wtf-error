"""Tests for the investigation orchestration service.

Fakes deliberately mirror the real runtime surfaces:

- ``FakeD1Database`` behaves like the Cloudflare Python Workers D1
  binding (``db.prepare(q).bind(*params)`` -> ``await .run()/.all()/
  .first()``, attribute-style rows, errors propagate). The SQLite schema
  is loaded from the real migration files.
- ``FakeAI`` behaves like the Workers AI binding: ``await ai.run(model,
  inputs)`` where ``inputs`` is a plain dict with a ``messages`` key,
  returning an attribute-style object with a ``response`` string field
  (matching ``ai-api-test.py`` in cloudflare/workerd). A dict-style
  variant is also exercised since the FFI shape may surface either way.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MIGRATIONS = ROOT / "migrations"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import investigation
from investigation import IncidentNotFoundError, investigate_incident


class FakeD1Result:
    def __init__(self, results: list[types.SimpleNamespace]) -> None:
        self.results = results


class FakeD1BoundStatement:
    def __init__(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: tuple[object, ...],
    ) -> None:
        self._conn = conn
        self._query = query
        self._params = params

    async def run(self) -> FakeD1Result:
        self._conn.execute(self._query, self._params)
        self._conn.commit()
        return FakeD1Result([])

    async def all(self) -> FakeD1Result:
        cur = self._conn.execute(self._query, self._params)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [types.SimpleNamespace(**dict(zip(cols, r))) for r in cur.fetchall()]
        return FakeD1Result(rows)

    async def first(self) -> types.SimpleNamespace | None:
        result = await self.all()
        return result.results[0] if result.results else None


class FakeD1PreparedStatement:
    def __init__(self, conn: sqlite3.Connection, query: str) -> None:
        self._conn = conn
        self._query = query

    def bind(self, *params: object) -> FakeD1BoundStatement:
        return FakeD1BoundStatement(self._conn, self._query, params)


class FakeD1Database:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def prepare(self, query: str) -> FakeD1PreparedStatement:
        return FakeD1PreparedStatement(self._conn, query)


class FakeAI:
    """Attribute-style Workers AI response (``resp.response``)."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self._payload = payload

    async def run(
        self, model: str, inputs: dict[str, object]
    ) -> types.SimpleNamespace:
        self.calls.append((model, inputs))
        return types.SimpleNamespace(response=json.dumps(self._payload))


class FakeDictAI(FakeAI):
    """Dict-style Workers AI response (``resp['response']``)."""

    async def run(self, model: str, inputs: dict[str, object]) -> dict[str, str]:
        self.calls.append((model, inputs))
        return {"response": json.dumps(self._payload)}


class FailingAI:
    async def run(
        self, model: str, inputs: dict[str, object]
    ) -> types.SimpleNamespace:
        raise RuntimeError("Workers AI is unavailable")


def _load_schema(conn: sqlite3.Connection) -> None:
    for name in (
        "0001_create_incidents.sql",
        "0002_create_messages.sql",
        "0003_create_findings.sql",
        "0004_create_evidence_and_finding_refs.sql",
    ):
        conn.executescript((MIGRATIONS / name).read_text())


PAYLOAD = {
    "analysis": "502s point at the backend not accepting connections.",
    "possible_causes": ["backend down", "wrong listen address"],
    "next_steps": ["check systemd status", "curl localhost:8000"],
    "findings": [],
}


class InvestigationServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        _load_schema(self.conn)
        self.conn.execute(
            "INSERT INTO incidents "
            "(id, title, symptoms, environment, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "inc-1",
                "Nginx returns 502",
                "Every API request returns 502 after restarting the backend.",
                "Ubuntu server, Nginx, FastAPI as systemd service.",
                "open",
                "2026-09-27T10:00:00+00:00",
                "2026-09-27T10:00:00+00:00",
            ),
        )
        self.conn.execute(
            "INSERT INTO messages "
            "(id, incident_id, role, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "msg-1",
                "inc-1",
                "user",
                "The backend logs show connection refused.",
                "2026-09-27T10:01:00+00:00",
                "2026-09-27T10:01:00+00:00",
            ),
        )
        self.conn.execute(
            "INSERT INTO findings (id, incident_id, title, detail, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "find-1",
                "inc-1",
                "Backend not listening",
                "Nothing on port 8000.",
                "2026-09-27T10:05:00+00:00",
            ),
        )
        self.conn.commit()
        self.db = FakeD1Database(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    async def test_happy_path_returns_structured_result(self) -> None:
        ai = FakeAI(dict(PAYLOAD))
        result = await investigate_incident(self.db, ai, "inc-1")
        self.assertEqual(result, PAYLOAD)
        self.assertEqual(
            set(result.keys()),
            {"analysis", "possible_causes", "next_steps", "findings"},
        )

    async def test_default_model_is_used_unless_overridden(self) -> None:
        ai = FakeAI(dict(PAYLOAD))
        await investigate_incident(self.db, ai, "inc-1")
        self.assertEqual(ai.calls[0][0], investigation.DEFAULT_MODEL)

        ai2 = FakeAI(dict(PAYLOAD))
        await investigate_incident(
            self.db, ai2, "inc-1", model="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        )
        self.assertEqual(
            ai2.calls[0][0], "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        )

    async def test_context_includes_incident_history_and_findings(self) -> None:
        ai = FakeAI(dict(PAYLOAD))
        await investigate_incident(self.db, ai, "inc-1")
        _, inputs = ai.calls[0]
        messages = inputs["messages"]
        assert isinstance(messages, list)
        roles = [m["role"] for m in messages]
        self.assertIn("system", roles)
        user_text = next(m["content"] for m in messages if m["role"] == "user")
        for expected in (
            "Nginx returns 502",  # title
            "Every API request returns 502",  # symptoms
            "Ubuntu server",  # environment
            "open",  # status
            "connection refused",  # previous message content
            "user",  # previous message role
            "Backend not listening",  # finding title
            "Nothing on port 8000.",  # finding detail
        ):
            self.assertIn(expected, user_text)

    async def test_missing_incident_raises_clear_error(self) -> None:
        ai = FakeAI(dict(PAYLOAD))
        with self.assertRaises(IncidentNotFoundError) as ctx:
            await investigate_incident(self.db, ai, "inc-missing")
        self.assertIn("inc-missing", str(ctx.exception))
        self.assertEqual(ai.calls, [])

    async def test_dict_style_ai_response_is_accepted(self) -> None:
        ai = FakeDictAI(dict(PAYLOAD))
        result = await investigate_incident(self.db, ai, "inc-1")
        self.assertEqual(result, PAYLOAD)

    async def test_model_errors_surface(self) -> None:
        with self.assertRaises(RuntimeError):
            await investigate_incident(self.db, FailingAI(), "inc-1")

    async def test_non_json_model_output_raises(self) -> None:
        class PlainTextAI:
            async def run(
                self, model: str, inputs: dict[str, object]
            ) -> types.SimpleNamespace:
                return types.SimpleNamespace(response="just some prose")

        with self.assertRaises(ValueError):
            await investigate_incident(self.db, PlainTextAI(), "inc-1")

    async def test_assistant_result_is_persisted(self) -> None:
        ai = FakeAI(dict(PAYLOAD))
        await investigate_incident(self.db, ai, "inc-1")
        messages = self.conn.execute(
            "SELECT role, content FROM messages ORDER BY created_at, id"
        ).fetchall()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[-1][0], "assistant")
        self.assertIn(PAYLOAD["analysis"], messages[-1][1])
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0], 1
        )


if __name__ == "__main__":
    unittest.main()
