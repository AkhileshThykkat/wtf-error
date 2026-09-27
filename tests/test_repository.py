"""Tests for messages + findings repository functions.

The fakes here deliberately behave like the real Cloudflare Python
Workers D1 binding, not like generic mocks:

- ``db.prepare(query).bind(*params)`` returns a bound statement.
- ``await bound.run()`` executes writes.
- ``await bound.all()`` returns a ``D1Result``-like object whose
  ``results`` attribute is a list of attribute-style rows
  (``row.id``, ``row.content``, ...), matching the Python Workers FFI.
- ``await bound.first()`` returns a single attribute-style row or None.
- Errors propagate; nothing is swallowed.

The SQLite schema is loaded from the real migration files so column
names are verified against the actual tables.
"""

from __future__ import annotations

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

import repository as repo


class FakeD1Result:
    def __init__(self, results: list[types.SimpleNamespace]) -> None:
        self.results = results


class FakeD1BoundStatement:
    def __init__(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: tuple[object, ...],
        recorder: list[tuple[str, tuple[object, ...]]],
    ) -> None:
        self._conn = conn
        self._query = query
        self._params = params
        self._recorder = recorder

    async def run(self) -> FakeD1Result:
        self._recorder.append((self._query, self._params))
        self._conn.execute(self._query, self._params)
        self._conn.commit()
        return FakeD1Result([])

    async def all(self) -> FakeD1Result:
        self._recorder.append((self._query, self._params))
        cur = self._conn.execute(self._query, self._params)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [types.SimpleNamespace(**dict(zip(cols, r))) for r in cur.fetchall()]
        return FakeD1Result(rows)

    async def first(self) -> types.SimpleNamespace | None:
        result = await self.all()
        return result.results[0] if result.results else None


class FakeD1PreparedStatement:
    def __init__(
        self,
        conn: sqlite3.Connection,
        query: str,
        recorder: list[tuple[str, tuple[object, ...]]],
    ) -> None:
        self._conn = conn
        self._query = query
        self._recorder = recorder

    def bind(self, *params: object) -> FakeD1BoundStatement:
        return FakeD1BoundStatement(self._conn, self._query, params, self._recorder)


class FakeD1Database:
    """SQLite-backed stand-in exposing only the real D1 surface."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.queries: list[tuple[str, tuple[object, ...]]] = []

    def prepare(self, query: str) -> FakeD1PreparedStatement:
        return FakeD1PreparedStatement(self._conn, query, self.queries)


class FailingD1Database:
    """Mimics a D1 binding whose prepare() itself fails."""

    def prepare(self, query: str) -> FakeD1PreparedStatement:
        raise RuntimeError("D1 is unavailable")


def _load_schema(conn: sqlite3.Connection) -> None:
    for name in (
        "0001_create_incidents.sql",
        "0002_create_messages.sql",
        "0003_create_findings.sql",
        "0004_create_evidence_and_finding_refs.sql",
    ):
        conn.executescript((MIGRATIONS / name).read_text())


class RepositoryMessagesFindingsTest(unittest.IsolatedAsyncioTestCase):
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
        self.conn.commit()
        self.db = FakeD1Database(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    async def test_create_message_inserts_all_fields(self) -> None:
        message = {
            "id": "msg-1",
            "incident_id": "inc-1",
            "role": "user",
            "content": "The backend logs show connection refused.",
            "created_at": "2026-09-27T10:01:00+00:00",
            "updated_at": "2026-09-27T10:01:00+00:00",
        }
        saved = await repo.create_message(self.db, message)
        self.assertEqual(saved, message)
        # Returned dict is a copy, not the caller's object.
        self.assertIsNot(saved, message)

        row = self.conn.execute(
            "SELECT id, incident_id, role, content, created_at, updated_at "
            "FROM messages WHERE id = ?",
            ("msg-1",),
        ).fetchone()
        self.assertEqual(
            row,
            (
                "msg-1",
                "inc-1",
                "user",
                "The backend logs show connection refused.",
                "2026-09-27T10:01:00+00:00",
                "2026-09-27T10:01:00+00:00",
            ),
        )

        query, _ = self.db.queries[-1]
        self.assertIn("INSERT INTO messages", query)
        self.assertIn("?", query)
        # Values travel via bind(), never interpolated into SQL.
        self.assertNotIn("connection refused", query)

    async def test_list_messages_orders_for_conversation_history(self) -> None:
        rows = [
            # Inserted out of order on purpose: same timestamp, ids reversed,
            # plus one earlier and one later timestamp.
            ("msg-c", "inc-1", "assistant", "third", "2026-09-27T10:03:00+00:00"),
            ("msg-b", "inc-1", "assistant", "second", "2026-09-27T10:02:00+00:00"),
            ("msg-a", "inc-1", "user", "first", "2026-09-27T10:02:00+00:00"),
            ("msg-other", "inc-9", "user", "elsewhere", "2026-09-27T10:01:00+00:00"),
        ]
        for mid, inc, role, content, ts in rows:
            self.conn.execute(
                "INSERT INTO messages "
                "(id, incident_id, role, content, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (mid, inc, role, content, ts, ts),
            )
        self.conn.execute(
            "INSERT INTO incidents "
            "(id, title, symptoms, environment, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "inc-9",
                "Other incident title",
                "Other incident symptoms are long enough.",
                "Other env",
                "open",
                "2026-09-27T10:00:00+00:00",
                "2026-09-27T10:00:00+00:00",
            ),
        )
        self.conn.commit()

        got = await repo.list_messages(self.db, "inc-1")
        self.assertEqual([m["id"] for m in got], ["msg-a", "msg-b", "msg-c"])
        self.assertTrue(all(isinstance(m, dict) for m in got))
        self.assertEqual(got[0]["content"], "first")

        query, _ = self.db.queries[-1]
        self.assertIn("WHERE incident_id = ?", query)
        self.assertIn("ORDER BY created_at ASC, id ASC", query)

    async def test_create_finding_inserts_all_fields(self) -> None:
        finding = {
            "id": "find-1",
            "incident_id": "inc-1",
            "title": "Backend not listening",
            "detail": "Service binds to 127.0.0.1 instead of 0.0.0.0.",
            "created_at": "2026-09-27T10:05:00+00:00",
        }
        saved = await repo.create_finding(self.db, finding)
        self.assertEqual(saved, finding)
        self.assertIsNot(saved, finding)

        row = self.conn.execute(
            "SELECT id, incident_id, title, detail, created_at "
            "FROM findings WHERE id = ?",
            ("find-1",),
        ).fetchone()
        self.assertEqual(
            row,
            (
                "find-1",
                "inc-1",
                "Backend not listening",
                "Service binds to 127.0.0.1 instead of 0.0.0.0.",
                "2026-09-27T10:05:00+00:00",
            ),
        )

        query, _ = self.db.queries[-1]
        self.assertIn("INSERT INTO findings", query)
        self.assertIn("?", query)
        self.assertNotIn("Backend not listening", query)

    async def test_list_findings_orders_and_isolates_incident(self) -> None:
        rows = [
            ("find-c", "inc-1", "C title", "C detail", "2026-09-27T10:03:00+00:00"),
            ("find-b", "inc-1", "B title", "B detail", "2026-09-27T10:02:00+00:00"),
            ("find-a", "inc-1", "A title", "A detail", "2026-09-27T10:02:00+00:00"),
            ("find-x", "inc-9", "X title", "X detail", "2026-09-27T10:01:00+00:00"),
        ]
        for fid, inc, title, detail, ts in rows:
            self.conn.execute(
                "INSERT INTO findings (id, incident_id, title, detail, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (fid, inc, title, detail, ts),
            )
        self.conn.commit()

        got = await repo.list_findings(self.db, "inc-1")
        self.assertEqual([f["id"] for f in got], ["find-a", "find-b", "find-c"])
        self.assertTrue(all(isinstance(f, dict) for f in got))

        query, _ = self.db.queries[-1]
        self.assertIn("WHERE incident_id = ?", query)
        self.assertIn("ORDER BY created_at ASC, id ASC", query)

    async def test_errors_are_not_swallowed(self) -> None:
        failing = FailingD1Database()
        with self.assertRaises(RuntimeError):
            await repo.create_message(
                failing,  # type: ignore[arg-type]
                {
                    "id": "msg-1",
                    "incident_id": "inc-1",
                    "role": "user",
                    "content": "hi, this message is long enough",
                    "created_at": "2026-09-27T10:01:00+00:00",
                    "updated_at": "2026-09-27T10:01:00+00:00",
                },
            )
        with self.assertRaises(RuntimeError):
            await repo.list_messages(failing, "inc-1")  # type: ignore[arg-type]
        with self.assertRaises(RuntimeError):
            await repo.create_finding(
                failing,  # type: ignore[arg-type]
                {
                    "id": "find-1",
                    "incident_id": "inc-1",
                    "title": "t",
                    "detail": "d",
                    "created_at": "2026-09-27T10:01:00+00:00",
                },
            )
        with self.assertRaises(RuntimeError):
            await repo.list_findings(failing, "inc-1")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
