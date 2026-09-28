# investigate_incident orchestration service

**Session ID:** ses_f1be489beffeD6Z6gobegL1g9E
**Created:** 9/27/2026, 11:53:20 PM
**Updated:** 9/27/2026, 11:55:38 PM

---

## User

The incident, message, and finding repositories are done.

Now create the first version of the investigation service.

Keep this focused on orchestration only.

Create something like:

`src/investigation.py`

Add one main function:

`investigate_incident(db, ai, incident_id)`

Its job is:

1. Load the incident using the repository.
2. If the incident does not exist, raise a clear error.
3. Load the previous messages for that incident.
4. Load the existing findings for that incident.
5. Build the context that will be sent to Workers AI.
6. Call the configured Workers AI model.
7. Return the AI result.

Do not add API route logic here.

Do not put raw SQL here.

Use the existing repository functions.

For this first version, do not make the AI perform a complex multi-step autonomous investigation.

Just make one clean model call using the incident and its history.

The prompt/context should include:

Incident:
- title
- symptoms
- environment
- status

Previous messages:
- role
- content

Existing findings:
- title
- evidence
- confidence

Tell the model that it is investigating a software/system incident.

The model should:

- analyze the symptoms
- identify likely causes
- explain its reasoning briefly
- suggest what should be checked next
- avoid pretending something was verified when it was not

For now, return a structured result from the service.

Something conceptually like:

{
    "analysis": "...",
    "next_steps": [...],
    "possible_causes": [...]
}

Use whatever response format works cleanly with the actual Cloudflare Workers AI Python binding.

Check Cloudflare documentation for the real Python Workers AI call shape instead of guessing.

Keep the Workers AI-specific code small and isolated.

Do not:

- create an ORM
- change database schemas
- add more tables
- add background jobs
- add agents
- add tool calling
- add loops
- add retries
- add RAG
- add embeddings
- add API endpoints yet
- silently swallow model errors

Let Workers AI errors surface for now.

Also do not store the AI response in `messages` or `findings` yet.

This step is only:

incident + history
        ↓
build context
        ↓
Workers AI
        ↓
structured investigation result

When finished, explain:

1. What file/function you added.
2. How incident/message/finding context is built.
3. Which Workers AI model is being called.
4. What exact response shape the service returns.
5. What Cloudflare documentation/binding behavior you relied on.
6. What tests you ran.
7. Whether you actually tested against Workers AI or only mocks/local tests.

Keep the implementation simple enough that the next step can add persistence of AI messages and findings. 

---

## Assistant (Build · Muse Spark 1.3 Free · 3.7s)

_Thinking:_



_Thinking:_



**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error</path>
<type>directory</type>
<entries>
.claude/
.git/
.gitignore
.python-version
.venv-workers/
.venv/
.wrangler/
migrations/
node_modules/
package-lock.json
package.json
prompt-history/
pylock.toml
pyproject.toml
pyrefly.toml
python_modules/
README.md
src/
tests/
uv.lock
wrangler.jsonc

(21 entries)
</entries>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.1s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/src</path>
<type>directory</type>
<entries>
__pycache__/
main.py
repository.py
schemas.py

(4 entries)
</entries>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/tests"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/tests</path>
<type>directory</type>
<entries>
__pycache__/
test_repository.py

(2 entries)
</entries>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/pyproject.toml"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/pyproject.toml</path>
<type>file</type>
<content>
1: [project]
2: name = "wtf-error"
3: version = "0.1.0"
4: description = "Add your description here"
5: readme = "README.md"
6: requires-python = ">=3.13"
7: dependencies = [
8:     "fastapi>=0.141.1",
9:     "pydantic>=2.13.5",
10:     "uvicorn>=0.54.0",
11: ]
12: 
13: [dependency-groups]
14: dev = [
15:     "pyrefly>=1.3.1",
16:     "workers-py>=1.17.4",
17:     "workers-runtime-sdk>=1.9.0",
18: ]

(End of file - total 18 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/wrangler.jsonc"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/wrangler.jsonc</path>
<type>file</type>
<content>
1: {
2:   "$schema": "node_modules/wrangler/config-schema.json",
3:   "name": "wtf-error",
4:   "main": "src/main.py",
5:   "compatibility_date": "2026-09-27",
6:   "compatibility_flags": ["python_workers"],
7:   "d1_databases": [
8:     {
9:       "binding": "DB",
10:       "database_name": "wtf-prod-db",
11:       "database_id": "53fac87a-8ebc-48e5-8fb6-b841c4ba74b2",
12:     },
13:   ],
14: }

(End of file - total 14 lines)
</content>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.2s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src/repository.py"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/src/repository.py</path>
<type>file</type>
<content>
1: """Repository helpers for incident records stored in Cloudflare D1.
2: 
3: Uses the D1 Python Workers async binding API (see
4: https://developers.cloudflare.com/d1/worker-api/prepared-statements and
5: https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers):
6: 
7:     await db.prepare("INSERT INTO ...").bind(...).run()
8:     await db.prepare("SELECT ... WHERE id = ?").bind(...).first()
9:     await db.prepare("SELECT ...").bind(...).all()
10: 
11: ``db`` is the D1 database binding (e.g. ``env.DB`` or, inside FastAPI,
12: ``request.scope["env"].DB``).
13: 
14: Per the Python Workers FFI, D1 rows come back as JavaScript objects
15: proxied into Python, so columns are read via attribute access
16: (``row.id``, ``row.title``, ...) as in the official
17: ``fastapi-todo`` / ``query-d1`` examples. ``all()`` returns a
18: ``D1Result`` whose ``results`` attribute is the list of rows, and
19: ``first()`` returns a single row object or ``None`` when no row matches.
20: Results are converted here into plain Python ``dict`` / ``list`` objects
21: so they are JSON-serializable.
22: 
23: All queries use parameterized SQL (``?`` placeholders + ``bind()``).
24: Errors are never swallowed: if D1 fails or conversion fails the
25: exception propagates to the caller.
26: """
27: 
28: from __future__ import annotations
29: 
30: from typing import Any
31: 
32: COLUMNS = "id, title, symptoms, environment, status, created_at, updated_at"
33: MESSAGE_COLUMNS = "id, incident_id, role, content, created_at, updated_at"
34: FINDING_COLUMNS = "id, incident_id, title, detail, created_at"
35: 
36: 
37: async def create_incident(db: Any, incident: dict[str, Any]) -> dict[str, Any]:
38:     """Insert a complete incident record and return it.
39: 
40:     ``incident`` is already a complete dictionary containing all 7 fields
41:     (``id``, ``title``, ``symptoms``, ``environment``, ``status``,
42:     ``created_at``, ``updated_at``). The caller provides the ID, status,
43:     and timestamps -- nothing is generated here.
44:     """
45:     await (
46:         db.prepare(
47:             "INSERT INTO incidents "
48:             "(id, title, symptoms, environment, status, created_at, updated_at) "
49:             "VALUES (?, ?, ?, ?, ?, ?, ?)"
50:         )
51:         .bind(
52:             incident["id"],
53:             incident["title"],
54:             incident["symptoms"],
55:             incident["environment"],
56:             incident["status"],
57:             incident["created_at"],
58:             incident["updated_at"],
59:         )
60:         .run()
61:     )
62:     return dict(incident)
63: 
64: 
65: async def get_incident(db: Any, incident_id: str) -> dict[str, Any] | None:
66:     """Return a single incident as a plain dict, or None if absent."""
67:     row = (
68:         await db.prepare(
69:             f"SELECT {COLUMNS} FROM incidents WHERE id = ? LIMIT 1"
70:         )
71:         .bind(incident_id)
72:         .first()
73:     )
74:     if row is None:
75:         return None
76:     return {
77:         "id": row.id,
78:         "title": row.title,
79:         "symptoms": row.symptoms,
80:         "environment": row.environment,
81:         "status": row.status,
82:         "created_at": row.created_at,
83:         "updated_at": row.updated_at,
84:     }
85: 
86: 
87: async def list_incidents(
88:     db: Any, limit: int = 20, offset: int = 0
89: ) -> list[dict[str, Any]]:
90:     """Return incidents ordered by created_at DESC, id DESC."""
91:     result = (
92:         await db.prepare(
93:             f"SELECT {COLUMNS} FROM incidents "
94:             "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
95:         )
96:         .bind(limit, offset)
97:         .all()
98:     )
99:     return [
100:         {
101:             "id": row.id,
102:             "title": row.title,
103:             "symptoms": row.symptoms,
104:             "environment": row.environment,
105:             "status": row.status,
106:             "created_at": row.created_at,
107:             "updated_at": row.updated_at,
108:         }
109:         for row in result.results
110:     ]
111: 
112: 
113: async def create_message(db: Any, message: dict[str, Any]) -> dict[str, Any]:
114:     """Insert a complete message record and return it.
115: 
116:     ``message`` is already a complete dictionary containing all 6 fields
117:     (``id``, ``incident_id``, ``role``, ``content``,
118:     ``created_at``, ``updated_at``). The caller provides the ID,
119:     incident ID, role, content, and timestamps -- nothing is generated
120:     here.
121:     """
122:     await (
123:         db.prepare(
124:             "INSERT INTO messages "
125:             "(id, incident_id, role, content, created_at, updated_at) "
126:             "VALUES (?, ?, ?, ?, ?, ?)"
127:         )
128:         .bind(
129:             message["id"],
130:             message["incident_id"],
131:             message["role"],
132:             message["content"],
133:             message["created_at"],
134:             message["updated_at"],
135:         )
136:         .run()
137:     )
138:     return dict(message)
139: 
140: 
141: async def list_messages(
142:     db: Any, incident_id: str
143: ) -> list[dict[str, Any]]:
144:     """Return messages for one incident, ordered for conversation history.
145: 
146:     Ordered by ``created_at ASC, id ASC`` so the result can be used
147:     directly as investigation conversation history.
148:     """
149:     result = (
150:         await db.prepare(
151:             f"SELECT {MESSAGE_COLUMNS} FROM messages "
152:             "WHERE incident_id = ? ORDER BY created_at ASC, id ASC"
153:         )
154:         .bind(incident_id)
155:         .all()
156:     )
157:     return [
158:         {
159:             "id": row.id,
160:             "incident_id": row.incident_id,
161:             "role": row.role,
162:             "content": row.content,
163:             "created_at": row.created_at,
164:             "updated_at": row.updated_at,
165:         }
166:         for row in result.results
167:     ]
168: 
169: 
170: async def create_finding(db: Any, finding: dict[str, Any]) -> dict[str, Any]:
171:     """Insert a complete finding record and return it.
172: 
173:     ``finding`` is already a complete dictionary containing all 5 fields
174:     (``id``, ``incident_id``, ``title``, ``detail``,
175:     ``created_at``). The caller provides all IDs, values, and
176:     timestamps -- nothing is generated here.
177:     """
178:     await (
179:         db.prepare(
180:             "INSERT INTO findings "
181:             "(id, incident_id, title, detail, created_at) "
182:             "VALUES (?, ?, ?, ?, ?)"
183:         )
184:         .bind(
185:             finding["id"],
186:             finding["incident_id"],
187:             finding["title"],
188:             finding["detail"],
189:             finding["created_at"],
190:         )
191:         .run()
192:     )
193:     return dict(finding)
194: 
195: 
196: async def list_findings(
197:     db: Any, incident_id: str
198: ) -> list[dict[str, Any]]:
199:     """Return findings for one incident ordered by created_at ASC, id ASC."""
200:     result = (
201:         await db.prepare(
202:             f"SELECT {FINDING_COLUMNS} FROM findings "
203:             "WHERE incident_id = ? ORDER BY created_at ASC, id ASC"
204:         )
205:         .bind(incident_id)
206:         .all()
207:     )
208:     return [
209:         {
210:             "id": row.id,
211:             "incident_id": row.incident_id,
212:             "title": row.title,
213:             "detail": row.detail,
214:             "created_at": row.created_at,
215:         }
216:         for row in result.results
217:     ]

(End of file - total 217 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src/schemas.py"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/src/schemas.py</path>
<type>file</type>
<content>
1: from pydantic import BaseModel, ConfigDict, Field
2: 
3: 
4: class IncidentCreate(BaseModel):
5:     model_config = ConfigDict(
6:         str_strip_whitespace=True,
7:         extra="forbid",
8:         json_schema_extra={
9:             "example": {
10:                 "title": "Nginx returns 502",
11:                 "symptoms": "Every API request returns 502 after restarting the backend.",
12:                 "environment": "Ubuntu server, Nginx, FastAPI running as a systemd service.",
13:             }
14:         },
15:     )
16: 
17:     title: str = Field(min_length=3, max_length=120)
18:     symptoms: str = Field(min_length=10, max_length=5000)
19:     environment: str = Field(min_length=3, max_length=1000)
20: 
21: 
22: class IncidentResponse(BaseModel):
23:     id: str
24:     title: str
25:     symptoms: str
26:     environment: str
27:     status: str
28:     created_at: str
29:     updated_at: str

(End of file - total 29 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src/main.py"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/src/main.py</path>
<type>file</type>
<content>
1: from datetime import datetime, timezone
2: from typing import Any
3: from uuid import uuid4
4: 
5: from fastapi import FastAPI, HTTPException, Query, Request
6: from workers import asgi
7: 
8: from repository import (
9:     create_incident as create_incident_in_db,
10: )
11: from repository import (
12:     get_incident as get_incident_from_db,
13: )
14: from repository import (
15:     list_incidents as list_incidents_from_db,
16: )
17: from schemas import IncidentCreate, IncidentResponse
18: 
19: app = FastAPI(title="wtf-error")
20: 
21: 
22: @app.get("/health")
23: async def health() -> dict[str, str]:
24:     return {"status": "ok", "service": "wtf-error"}
25: 
26: 
27: @app.post("/api/incidents", response_model=IncidentResponse, status_code=201)
28: async def create_incident(
29:     payload: IncidentCreate, request: Request
30: ) -> dict[str, Any]:
31:     db: Any = request.scope["env"].DB
32:     now: str = datetime.now(timezone.utc).isoformat()
33:     incident: dict[str, Any] = {
34:         "id": str(uuid4()),
35:         "title": payload.title,
36:         "symptoms": payload.symptoms,
37:         "environment": payload.environment,
38:         "status": "open",
39:         "created_at": now,
40:         "updated_at": now,
41:     }
42:     saved: dict[str, Any] = await create_incident_in_db(db, incident)
43:     return saved
44: 
45: 
46: @app.get("/api/incidents", response_model=list[IncidentResponse])
47: async def list_incidents(
48:     request: Request,
49:     limit: int = Query(default=20, ge=1, le=100),
50:     offset: int = Query(default=0, ge=0),
51: ) -> list[dict[str, Any]]:
52:     db: Any = request.scope["env"].DB
53:     return await list_incidents_from_db(db, limit, offset)
54: 
55: 
56: @app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
57: async def get_incident(incident_id: str, request: Request) -> dict[str, Any]:
58:     db: Any = request.scope["env"].DB
59:     incident: dict[str, Any] | None = await get_incident_from_db(db, incident_id)
60:     if incident is None:
61:         raise HTTPException(status_code=404, detail="Incident not found")
62:     return incident
63: 
64: 
65: Default = asgi.entrypoint(app)

(End of file - total 65 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/tests/test_repository.py"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/tests/test_repository.py</path>
<type>file</type>
<content>
1: """Tests for messages + findings repository functions.
2: 
3: The fakes here deliberately behave like the real Cloudflare Python
4: Workers D1 binding, not like generic mocks:
5: 
6: - ``db.prepare(query).bind(*params)`` returns a bound statement.
7: - ``await bound.run()`` executes writes.
8: - ``await bound.all()`` returns a ``D1Result``-like object whose
9:   ``results`` attribute is a list of attribute-style rows
10:   (``row.id``, ``row.content``, ...), matching the Python Workers FFI.
11: - ``await bound.first()`` returns a single attribute-style row or None.
12: - Errors propagate; nothing is swallowed.
13: 
14: The SQLite schema is loaded from the real migration files so column
15: names are verified against the actual tables.
16: """
17: 
18: from __future__ import annotations
19: 
20: import pathlib
21: import sqlite3
22: import sys
23: import types
24: import unittest
25: 
26: ROOT = pathlib.Path(__file__).resolve().parents[1]
27: SRC = ROOT / "src"
28: MIGRATIONS = ROOT / "migrations"
29: if str(SRC) not in sys.path:
30:     sys.path.insert(0, str(SRC))
31: 
32: import repository as repo
33: 
34: 
35: class FakeD1Result:
36:     def __init__(self, results: list[types.SimpleNamespace]) -> None:
37:         self.results = results
38: 
39: 
40: class FakeD1BoundStatement:
41:     def __init__(
42:         self,
43:         conn: sqlite3.Connection,
44:         query: str,
45:         params: tuple[object, ...],
46:         recorder: list[tuple[str, tuple[object, ...]]],
47:     ) -> None:
48:         self._conn = conn
49:         self._query = query
50:         self._params = params
51:         self._recorder = recorder
52: 
53:     async def run(self) -> FakeD1Result:
54:         self._recorder.append((self._query, self._params))
55:         self._conn.execute(self._query, self._params)
56:         self._conn.commit()
57:         return FakeD1Result([])
58: 
59:     async def all(self) -> FakeD1Result:
60:         self._recorder.append((self._query, self._params))
61:         cur = self._conn.execute(self._query, self._params)
62:         cols = [d[0] for d in cur.description] if cur.description else []
63:         rows = [types.SimpleNamespace(**dict(zip(cols, r))) for r in cur.fetchall()]
64:         return FakeD1Result(rows)
65: 
66:     async def first(self) -> types.SimpleNamespace | None:
67:         result = await self.all()
68:         return result.results[0] if result.results else None
69: 
70: 
71: class FakeD1PreparedStatement:
72:     def __init__(
73:         self,
74:         conn: sqlite3.Connection,
75:         query: str,
76:         recorder: list[tuple[str, tuple[object, ...]]],
77:     ) -> None:
78:         self._conn = conn
79:         self._query = query
80:         self._recorder = recorder
81: 
82:     def bind(self, *params: object) -> FakeD1BoundStatement:
83:         return FakeD1BoundStatement(self._conn, self._query, params, self._recorder)
84: 
85: 
86: class FakeD1Database:
87:     """SQLite-backed stand-in exposing only the real D1 surface."""
88: 
89:     def __init__(self, conn: sqlite3.Connection) -> None:
90:         self._conn = conn
91:         self.queries: list[tuple[str, tuple[object, ...]]] = []
92: 
93:     def prepare(self, query: str) -> FakeD1PreparedStatement:
94:         return FakeD1PreparedStatement(self._conn, query, self.queries)
95: 
96: 
97: class FailingD1Database:
98:     """Mimics a D1 binding whose prepare() itself fails."""
99: 
100:     def prepare(self, query: str) -> FakeD1PreparedStatement:
101:         raise RuntimeError("D1 is unavailable")
102: 
103: 
104: def _load_schema(conn: sqlite3.Connection) -> None:
105:     for name in (
106:         "0001_create_incidents.sql",
107:         "0002_create_messages.sql",
108:         "0003_create_findings.sql",
109:     ):
110:         conn.executescript((MIGRATIONS / name).read_text())
111: 
112: 
113: class RepositoryMessagesFindingsTest(unittest.IsolatedAsyncioTestCase):
114:     def setUp(self) -> None:
115:         self.conn = sqlite3.connect(":memory:")
116:         _load_schema(self.conn)
117:         self.conn.execute(
118:             "INSERT INTO incidents "
119:             "(id, title, symptoms, environment, status, created_at, updated_at) "
120:             "VALUES (?, ?, ?, ?, ?, ?, ?)",
121:             (
122:                 "inc-1",
123:                 "Nginx returns 502",
124:                 "Every API request returns 502 after restarting the backend.",
125:                 "Ubuntu server, Nginx, FastAPI as systemd service.",
126:                 "open",
127:                 "2026-09-27T10:00:00+00:00",
128:                 "2026-09-27T10:00:00+00:00",
129:             ),
130:         )
131:         self.conn.commit()
132:         self.db = FakeD1Database(self.conn)
133: 
134:     def tearDown(self) -> None:
135:         self.conn.close()
136: 
137:     async def test_create_message_inserts_all_fields(self) -> None:
138:         message = {
139:             "id": "msg-1",
140:             "incident_id": "inc-1",
141:             "role": "user",
142:             "content": "The backend logs show connection refused.",
143:             "created_at": "2026-09-27T10:01:00+00:00",
144:             "updated_at": "2026-09-27T10:01:00+00:00",
145:         }
146:         saved = await repo.create_message(self.db, message)
147:         self.assertEqual(saved, message)
148:         # Returned dict is a copy, not the caller's object.
149:         self.assertIsNot(saved, message)
150: 
151:         row = self.conn.execute(
152:             "SELECT id, incident_id, role, content, created_at, updated_at "
153:             "FROM messages WHERE id = ?",
154:             ("msg-1",),
155:         ).fetchone()
156:         self.assertEqual(
157:             row,
158:             (
159:                 "msg-1",
160:                 "inc-1",
161:                 "user",
162:                 "The backend logs show connection refused.",
163:                 "2026-09-27T10:01:00+00:00",
164:                 "2026-09-27T10:01:00+00:00",
165:             ),
166:         )
167: 
168:         query, _ = self.db.queries[-1]
169:         self.assertIn("INSERT INTO messages", query)
170:         self.assertIn("?", query)
171:         # Values travel via bind(), never interpolated into SQL.
172:         self.assertNotIn("connection refused", query)
173: 
174:     async def test_list_messages_orders_for_conversation_history(self) -> None:
175:         rows = [
176:             # Inserted out of order on purpose: same timestamp, ids reversed,
177:             # plus one earlier and one later timestamp.
178:             ("msg-c", "inc-1", "assistant", "third", "2026-09-27T10:03:00+00:00"),
179:             ("msg-b", "inc-1", "assistant", "second", "2026-09-27T10:02:00+00:00"),
180:             ("msg-a", "inc-1", "user", "first", "2026-09-27T10:02:00+00:00"),
181:             ("msg-other", "inc-9", "user", "elsewhere", "2026-09-27T10:01:00+00:00"),
182:         ]
183:         for mid, inc, role, content, ts in rows:
184:             self.conn.execute(
185:                 "INSERT INTO messages "
186:                 "(id, incident_id, role, content, created_at, updated_at) "
187:                 "VALUES (?, ?, ?, ?, ?, ?)",
188:                 (mid, inc, role, content, ts, ts),
189:             )
190:         self.conn.execute(
191:             "INSERT INTO incidents "
192:             "(id, title, symptoms, environment, status, created_at, updated_at) "
193:             "VALUES (?, ?, ?, ?, ?, ?, ?)",
194:             (
195:                 "inc-9",
196:                 "Other incident title",
197:                 "Other incident symptoms are long enough.",
198:                 "Other env",
199:                 "open",
200:                 "2026-09-27T10:00:00+00:00",
201:                 "2026-09-27T10:00:00+00:00",
202:             ),
203:         )
204:         self.conn.commit()
205: 
206:         got = await repo.list_messages(self.db, "inc-1")
207:         self.assertEqual([m["id"] for m in got], ["msg-a", "msg-b", "msg-c"])
208:         self.assertTrue(all(isinstance(m, dict) for m in got))
209:         self.assertEqual(got[0]["content"], "first")
210: 
211:         query, _ = self.db.queries[-1]
212:         self.assertIn("WHERE incident_id = ?", query)
213:         self.assertIn("ORDER BY created_at ASC, id ASC", query)
214: 
215:     async def test_create_finding_inserts_all_fields(self) -> None:
216:         finding = {
217:             "id": "find-1",
218:             "incident_id": "inc-1",
219:             "title": "Backend not listening",
220:             "detail": "Service binds to 127.0.0.1 instead of 0.0.0.0.",
221:             "created_at": "2026-09-27T10:05:00+00:00",
222:         }
223:         saved = await repo.create_finding(self.db, finding)
224:         self.assertEqual(saved, finding)
225:         self.assertIsNot(saved, finding)
226: 
227:         row = self.conn.execute(
228:             "SELECT id, incident_id, title, detail, created_at "
229:             "FROM findings WHERE id = ?",
230:             ("find-1",),
231:         ).fetchone()
232:         self.assertEqual(
233:             row,
234:             (
235:                 "find-1",
236:                 "inc-1",
237:                 "Backend not listening",
238:                 "Service binds to 127.0.0.1 instead of 0.0.0.0.",
239:                 "2026-09-27T10:05:00+00:00",
240:             ),
241:         )
242: 
243:         query, _ = self.db.queries[-1]
244:         self.assertIn("INSERT INTO findings", query)
245:         self.assertIn("?", query)
246:         self.assertNotIn("Backend not listening", query)
247: 
248:     async def test_list_findings_orders_and_isolates_incident(self) -> None:
249:         rows = [
250:             ("find-c", "inc-1", "C title", "C detail", "2026-09-27T10:03:00+00:00"),
251:             ("find-b", "inc-1", "B title", "B detail", "2026-09-27T10:02:00+00:00"),
252:             ("find-a", "inc-1", "A title", "A detail", "2026-09-27T10:02:00+00:00"),
253:             ("find-x", "inc-9", "X title", "X detail", "2026-09-27T10:01:00+00:00"),
254:         ]
255:         for fid, inc, title, detail, ts in rows:
256:             self.conn.execute(
257:                 "INSERT INTO findings (id, incident_id, title, detail, created_at) "
258:                 "VALUES (?, ?, ?, ?, ?)",
259:                 (fid, inc, title, detail, ts),
260:             )
261:         self.conn.commit()
262: 
263:         got = await repo.list_findings(self.db, "inc-1")
264:         self.assertEqual([f["id"] for f in got], ["find-a", "find-b", "find-c"])
265:         self.assertTrue(all(isinstance(f, dict) for f in got))
266: 
267:         query, _ = self.db.queries[-1]
268:         self.assertIn("WHERE incident_id = ?", query)
269:         self.assertIn("ORDER BY created_at ASC, id ASC", query)
270: 
271:     async def test_errors_are_not_swallowed(self) -> None:
272:         failing = FailingD1Database()
273:         with self.assertRaises(RuntimeError):
274:             await repo.create_message(
275:                 failing,  # type: ignore[arg-type]
276:                 {
277:                     "id": "msg-1",
278:                     "incident_id": "inc-1",
279:                     "role": "user",
280:                     "content": "hi, this message is long enough",
281:                     "created_at": "2026-09-27T10:01:00+00:00",
282:                     "updated_at": "2026-09-27T10:01:00+00:00",
283:                 },
284:             )
285:         with self.assertRaises(RuntimeError):
286:             await repo.list_messages(failing, "inc-1")  # type: ignore[arg-type]
287:         with self.assertRaises(RuntimeError):
288:             await repo.create_finding(
289:                 failing,  # type: ignore[arg-type]
290:                 {
291:                     "id": "find-1",
292:                     "incident_id": "inc-1",
293:                     "title": "t",
294:                     "detail": "d",
295:                     "created_at": "2026-09-27T10:01:00+00:00",
296:                 },
297:             )
298:         with self.assertRaises(RuntimeError):
299:             await repo.list_findings(failing, "inc-1")  # type: ignore[arg-type]
300: 
301: 
302: if __name__ == "__main__":
303:     unittest.main()

(End of file - total 303 lines)
</content>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.6s)

_Thinking:_



**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/migrations"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/migrations</path>
<type>directory</type>
<entries>
0001_create_incidents.sql
0002_create_messages.sql
0003_create_findings.sql

(3 entries)
</entries>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/README.md"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/README.md</path>
<type>file</type>
<content>


(End of file - total 0 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/package.json"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/package.json</path>
<type>file</type>
<content>
1: {
2:   "dependencies": {
3:     "wrangler": "^4.142.0"
4:   }
5: }

(End of file - total 5 lines)
</content>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.4s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/migrations/0001_create_incidents.sql"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/migrations/0001_create_incidents.sql</path>
<type>file</type>
<content>
1: -- Migration number: 0001 	 2026-09-27T17:51:00.221Z
2: CREATE TABLE incidents (
3:     id TEXT PRIMARY KEY NOT NULL,
4:     title TEXT NOT NULL,
5:     symptoms TEXT NOT NULL,
6:     environment TEXT NOT NULL,
7: 
8:     status TEXT NOT NULL DEFAULT 'open'
9:         CHECK (status IN ('open', 'investigating', 'resolved')),
10: 
11:     created_at TEXT NOT NULL,
12:     updated_at TEXT NOT NULL
13: );
14: 
15: CREATE INDEX idx_incidents_created_at_id
16:     ON incidents (created_at DESC, id DESC);

(End of file - total 16 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/migrations/0002_create_messages.sql"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/migrations/0002_create_messages.sql</path>
<type>file</type>
<content>
1: -- Migration number: 0002 	 2026-09-27T18:00:00.000Z
2: CREATE TABLE messages (
3:     id TEXT PRIMARY KEY NOT NULL,
4:     incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
5:     role TEXT NOT NULL
6:         CHECK (role IN ('user', 'assistant', 'system')),
7:     content TEXT NOT NULL,
8:     created_at TEXT NOT NULL,
9:     updated_at TEXT NOT NULL
10: );
11: 
12: CREATE INDEX idx_messages_incident_created_id
13:     ON messages (incident_id, created_at ASC, id ASC);

(End of file - total 13 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/migrations/0003_create_findings.sql"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/migrations/0003_create_findings.sql</path>
<type>file</type>
<content>
1: -- Migration number: 0003 	 2026-09-27T18:00:00.000Z
2: CREATE TABLE findings (
3:     id TEXT PRIMARY KEY NOT NULL,
4:     incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
5:     title TEXT NOT NULL,
6:     detail TEXT NOT NULL,
7:     created_at TEXT NOT NULL
8: );
9: 
10: CREATE INDEX idx_findings_incident_created_id
11:     ON findings (incident_id, created_at ASC, id ASC);

(End of file - total 11 lines)
</content>
```

**Tool: bash**

**Input:**
```json
{
  "command": "ls prompt-history/ 2>/dev/null; ls .venv/ 2>/dev/null | head; python3 --version; pip list 2>/dev/null | grep -i -E \"worker|fastapi\" | head -20"
}
```

**Output:**
```
incident_related_api_creation.md
repository_creation.md
repository_refactor.md
update repository.md
bin
CACHEDIR.TAG
lib
lib64
pyvenv.cfg
Python 3.14.7

```

---

## Assistant (Build · Muse Spark 1.3 Free · 4.3s)

_Thinking:_



_Thinking:_



**Tool: websearch**

**Input:**
```json
{
  "contextMaxCharacters": 12000,
  "numResults": 8,
  "query": "Cloudflare Workers AI Python binding run model workers-py 2026",
  "type": "deep"
}
```

**Output:**
```
Title: Workers Bindings · Cloudflare AI Gateway docs
URL: https://developers.cloudflare.com/ai-gateway/usage/worker-binding-methods/
Published: N/A
Author: N/A
Highlights:
The AI binding (`env.AI`) lets you call AI models and access AI Gateway features directly from your Worker.
...
to your Wrangler configuration file
...
The binding is accessible in your Worker code as `env.AI`.

If you're using TypeScript, run `wrangler types` whenever you modify your Wrangler configuration file. This generates types for the `env` object based on your bindings, as well as runtime types.

## `env.AI.run()`

Runs an inference request through AI Gateway. Accepts Workers AI models (`@cf/` prefix) and third-party models (`{author}/{model}` format).

Workers AI model:

```
const resp = await env.AI.run(
	"@cf/moonshotai/kimi-k2.5",
	{
		prompt: "tell me a joke",
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
...
To use prepaid AI Gateway credits, set the gateway's Workers AI billing setting to Unified billing and specify that gateway in the binding request. Prepaid credits provide access to Workers AI models that otherwise require the Workers Paid plan and provide higher rate limits for frontier models.
...
Third-party models require an AI Gateway and use Unified Billing. Cloudflare manages the provider credentials and deducts credits from your account. You do not need to supply your own API keys.

On the AI binding path, only a BYOK (Bring Your Own Keys) key stored under the `default` alias is used. Keys stored under other aliases are not consulted, and the request falls through to Unified Billing. To select a non-default alias, use the provider-native endpoints with the `cf-aig-byok-alias` header. See credential precedence for details.
...
### Gateway options

The third argument to `env.AI.run()` accepts a `gateway` object with the following parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `string` | required | Name of your AI Gateway. Must be in the same account as your Worker. Use `"default"` to automatically create a gateway on the first authenticated request. Refer to Default gateway for details. |
| `skipCache` | `boolean` | `false` | Skip the cache for this request. |
| `cacheTtl` | `number` | — | Cache TTL in seconds. |
| `cacheKey` | `string` | — | Custom cache key for this request. |
| `collectLog` | `boolean` | — | Whether to collect logs for this request. |
| `metadata` | `object` | — | Custom metadata to attach to the log entry. |
...
## `env.AI.gateway()`

Returns a gateway instance for accessing AI Gateway methods directly.

---

Title: Set up Workers AI with AI Gateway · Cloudflare AI Gateway docs
URL: https://developers.cloudflare.com/ai-gateway/integrations/aig-workers-ai-binding/
Published: N/A
Author: N/A
Highlights:
This guide will walk you through setting up and deploying a Workers AI project. You will use Workers, an AI Gateway binding, and a large language model (LLM), to deploy your first AI-powered application on the Cloudflare global network.
...
## 2. Connect your Worker to Workers AI

You must create an AI binding for your Worker to connect to Workers AI. Bindings allow your Workers to interact with resources, like Workers AI, on the Cloudflare Developer Platform.

To bind Workers AI to your Worker, add the following to the end of your Wrangler configuration file:

```
{
	"ai": {
		"binding": "AI",
	},
}
```
...
```
[ai]
binding = "AI"
...
Your binding is available in your Worker code on `env.AI`.

You can use `"default"` as the gateway ID in the next step. AI Gateway automatically creates a default gateway on the first authenticated request. Alternatively, you can create a gateway manually and use its ID.

## 3. Run an inference task containing AI Gateway in your Worker

You are now ready to run an inference task in your Worker. In this case, you will use an LLM, `llama-3.1-8b-instruct-fast`, to answer a question.

Update the `index.ts` file in your `hello-ai` application directory with the following code:
...
```
export interface Env {
	// If you set another name in the [Wrangler configuration file](/workers/wrangler/configuration/) as the value for 'binding',
	// replace "AI" with the variable name you defined.
	AI: Ai;
}

export default {
	async fetch(request, env): Promise<Response> {
		// Specify the gateway label and other options here
		const response = await env.AI.run(
			"@cf/meta/llama-3.1-8b-instruct-fast",
			{
				prompt: "What is the origin of the phrase Hello, World",
			},
			{
				gateway: {
					id: "default", // Uses the default gateway, or replace with your gateway ID
					skipCache: true, // Optional: Skip cache if needed
				},
			},
		);

		// Return the AI response as a JSON object
		return new Response(JSON.stringify(response), {
			headers: { "Content-Type": "application/json" },
		});
	},
} satisfies ExportedHandler<Env>;
```
...
Up to this point, you have created an AI binding for your Worker and configured your Worker to be able to execute the Llama 3.1 model. You can now test your project locally before you deploy globally.
...
While in your project directory, test Workers AI locally by running `wrangler dev`:

```
npx wrangler dev
...
always accesses your Cloudflare account in order to run AI models and will incur usage ... even in local development.
...
## 5. Deploy your AI Worker

Before deploying your AI Worker globally, log in with your Cloudflare account by running:
...
Finally, deploy your Worker to make your project accessible on the Internet. To deploy your Worker, run:

```
npx wrangler deploy
...
By completing this tutorial, you have created a Worker, connected it to Workers AI through an AI Gateway binding, and successfully ran an inference task using the Llama 3.1 model.

---

Title: N/A
URL: https://developers.cloudflare.com/workers-ai/index.md
Published: N/A
Author: N/A
Highlights:
# Cloudflare Workers AI

Last updated Apr 21, 2026|Copy as Markdown| View as Markdown| Agent setup

Run machine learning models, powered by serverless GPUs, on Cloudflare's global network.
...
Workers AI allows you to run AI models in a serverless way, without having to worry about scaling, maintaining, or paying for unused infrastructure. You can invoke models running on GPUs on Cloudflare's network from your own code — from Workers, Pages, or anywhere via the Cloudflare API.
...
50+ open ... source models, available as a part of
...
Serverless, pay ... -use pricing
...
All as part of
...
Workers AI is now
...
Workers AI comes with a curated set of popular open-source models that enable you to do tasks such as image classification, text generation, object detection and more.
...
Build and deploy your first Workers AI application.

---

Title: Execute AI model | Cloudflare API
URL: https://developers.cloudflare.com/api/python/resources/ai/methods/run/
Published: N/A
Author: N/A
Highlights:
ai. run(str model_name, AIRunParams**kwargs) -> AIRunResponse

POST/accounts/{account_id}/ai/run/{model_name}

This endpoint provides users with the capability to run specific AI models on-demand.

By submitting the required input data, users can receive real-time predictions or results generated by the chosen AI model. The endpoint supports various AI model types, ensuring flexibility and adaptability for diverse use cases.
...
`Workers AI Write``Workers AI Read`

##### Parameters Expand Collapse 

account_id: str

model_name: str

text: str

The text that you want to classify

minLength 1
...
### Execute AI model

```
import os
from cloudflare import Cloudflare

client = Cloudflare(
    api_token=os.environ.get("CLOUDFLARE_API_TOKEN"),  # This is the default and can be omitted
)
response = client.ai.run(
    model_name="model_name",
    account_id="023e105f4ecef8ad9ca31a8372d0c353",
    text="x",
)
print(response)

---

Title: ai/packages/workers-ai-provider at main · cloudflare/ai · GitHub
URL: https://github.com/cloudflare/ai/tree/main/packages/workers-ai-provider
Published: 2025-03-14T12:57:48.000Z
Author: cloudflare
Highlights:
Workers AI provider for the AI SDK. Run Cloudflare's models for chat, embeddings, image generation, transcription, text-to-speech, reranking, and AI Search— all from a single provider. It can also route third-party models (OpenAI, Anthropic, Google, …) through AI Gateway— see Third-party models.
...
```
npm install workers-ai-provider ai
...
```
// wrangler.jsonc
{
	"ai": { "binding": "AI" },
}
...
```
import { createWorkersAI } from "workers-ai-provider";
import { streamText } from "ai";

export default {
	async fetch(req: Request, env: { AI: Ai }) {
		const workersai = createWorkersAI({ binding: env.AI });

		const result = streamText({
			model: workersai("@cf/moonshotai/kimi-k2.7-code"),
			messages: [{ role: "user", content: "Write a haiku about Cloudflare" }],
		});

		return result.toTextStreamResponse();
	},
};
```
...
### Workers binding (recommended)

Inside a Cloudflare Worker, pass the`env.AI` binding directly. No API keys needed.

```
const workersai = createWorkersAI({ binding: env.AI });
```
...
Browse the full catalog at developers.cloudflare.com/workers-ai/models.
...
| Task | Model | Notes |
| --- | --- | --- |
| Chat | `@cf/moonshotai/kimi-k2.7-code` | 256k ctx, tools, vision, reasoning |
| Chat | `@cf/zai-org/glm-4.7-flash` | Fast, multilingual, 131k ctx |
| Chat | `@cf/openai/gpt-oss-120b` | OpenAI open-weights, high reasoning |
| Reasoning | `@cf/moonshotai/kimi-k2.7-code` | Configurable`reasoning_effort` |
| Reasoning | `@cf/qwen/qwq-32b` | Emits`reasoning_content` |
| Embeddings | `@cf/baai/bge-base-en-v1.5` | 768-dim, English |
| Embeddings | `@cf/google/embeddinggemma-300m` | 100+ languages, by Google |
| Images | `@cf/black-forest-labs/flux-1-schnell` | Fast, free-tier image generation |
| Transcription | `@cf/openai/whisper-large-v3-turbo` | Best accuracy, multilingual |
| Transcription | `@cf/deepgram/nova-3` | Fast, high accuracy |
| Text-to-Speech | `@cf/deepgram/aura-2-en` | Context-aware, natural pacing |
| Reranking | `@cf/baai/bge-reranker-base` | Fast document reranking |
...
— OpenAI, Anthropic ... — through AI Gateway using the same`env.AI` binding,
...
Pass the plugins to`createWorkersAI` via`providers`. Then it's the same provider you already use:`@cf/...` ids build Workers AI models, and a`" / "` catalog slug is routed through AI Gateway automatically.`createWorkersAI` is the single public entry point — there's no separate factory to import.

```
import { createWorkersAI } from "workers-ai-provider";
import { openai } from "workers-ai-provider/openai";
import { anthropic } from "workers-ai-provider/anthropic";
import { streamText } from "ai";

const workersai = createWorkersAI({
	binding: env.AI,
	providers: [openai, anthropic], // opt-in; enables third-party routing
	// gateway is optional — catalog routing uses your account's "default"
	// gateway unless you set one, e.g. gateway: { id: "my-gateway" }.
});

workersai("@cf/zai-org/glm-5.2"); // Workers AI (unchanged)
...
The settings argument is typed from the model id: pass a`" / "` catalog slug and the second argument autocompletes the per-call gateway options (`resume`,`fallback`,`cacheTtl`,`byok`,`metadata`, …, i.e.`DelegateCallOptions`); pass a`@cf/...` id and it autocompletes the usual`WorkersAIChatSettings`.`providers` is optional and additive: leave it unset and`createWorkersAI` behaves exactly as before —`@cf/...` ids work as always, and a`" / "` catalog slug still routes through the unified-billing run path (defaulting to your account's`"default"` gateway, with the built-in OpenAI-compatible parser). Configure`providers` to unlock higher-fidelity parsing plus the per-call delegate options (BYOK, caching, fallback, resume); requesting one of those without`providers` throws a helpful error pointing you here.
...
| Transport | Backed by | Resume (coming soon) (`cf-aig-run-id`) | Caching | Server fallback | Billing |
| --- | --- | --- | --- | --- | --- |
| run (default) | `env.AI.run(...)` | ✅ | ❌ | ❌ | Unified billing |
| gateway | `env.AI.gateway(id).run([])` | ❌ | ✅ | ✅ | BYOK / stored key |

Run-catalog providers (OpenAI, Anthropic, Google, xAI, Groq, DeepSeek, plus the unified-catalog chat providers Alibaba/Qwen and MiniMax) default to the resumable run path. BYOK-only providers (mistral, perplexity, cerebras, …) always use the gateway path. Asking for an impossible combination (e.g.`resume: true` with`fallback.mode: "server"`) throws a`GatewayDelegateError`.
...
## API reference

### createWorkersAI(options)

| Option | Type | Description |
| --- | --- | --- |
| `binding` | `Ai` | Workers AI binding (`env.AI`). Use this OR credentials. |
| `accountId` | `string` | Cloudflare account ID. Required with`apiKey`. |
| `apiKey` | `string` | Cloudflare API token. Required with`accountId`. |
| `gateway` | `GatewayOptions` | Optional AI Gateway config. |
| `providers` | `ProviderPlugin[]` | Experimental. Wire-format plugins that enable routing`" / "` slugs via gateway. |
| `resume` | `boolean` | Experimental — coming soon. Default resume behavior for gateway-routed catalog models. Defaults to`true`. |
| `onResumeExpired` | `"error"`|`"accept-partial"` | Experimental — coming soon. Default policy when the gateway resume buffer expires. Defaults to`"error"`. |

Returns a provider with model factories. Each factory accepts an optional second argument for per-model settings:
...
Model factories:

```
// Chat — for generateText / streamText (also accepts third-party slugs when `providers` is set)
workersai(modelId);
workersai.chat(modelId);

// Embeddings — for embedMany / embed
workersai.textEmbedding(modelId);

// Images — for generateImage
workersai.image(modelId);

// Transcription — for transcribe
workersai.transcription(modelId, settings?);

// Text-to-Speech — for speech
workersai.speech(modelId);

// Reranking — for rerank
workersai.reranking(modelId);
...
### createAISearch(options)

| Option | Type | Description |
| --- | --- | ---
...
RAG` | ... Search binding (`

---

Title: cloudflare/python-workers-examples
URL: https://github.com/cloudflare/python-workers-examples
Published: N/A
Author: N/A
Highlights:
You can run `uvx --from workers-py pywrangler dev` in any example project directory to run a local development server using Pywrangler, the CLI for Cloudflare Python Workers. This local development server is powered by workerd, the open-source Workers runtime.
...
- **`binding/`** — shows how bindings work in Python Workers. Put a key into Workers KV, and then read it.
...
- **`workers-ai/`** makes a call Workers AI to run inference on Cloudflare's Global Network.
...
- **`dynamic-py-py/`** — shows how to load and run a Python Worker dynamically at runtime using a Worker Loader binding.
...
- You must add the `python_workers` compatibility flag to your Worker while Python Workers are in open beta.

---

Title: N/A
URL: https://developers.cloudflare.com/workers/languages/python/ffi/index.md
Published: N/A
Author: N/A
Highlights:
Via Pyodide ↗, Python Workers provide a Foreign Function Interface (FFI) ↗ to JavaScript. This allows you to:

- Use bindings to resources on Cloudflare, including Workers AI, Vectorize, R2, KV, D1, Queues, Durable Objects, Service Bindings and more.
- Use JavaScript globals, like Request, Response, and fetch().
- Use the full feature set of Cloudflare Workers — if an API is accessible in JavaScript, you can also access it in a Python Worker, writing exclusively Python code.

The details of Pyodide's Foreign Function Interface are documented here ↗, and Workers written in Python are able to take full advantage of this.

## Using Bindings from Python Workers

Bindings allow your Worker to interact with resources on the Cloudflare Developer Platform. When you declare a binding on your Worker, you grant it a specific capability, such as being able to read and write files to an R2 bucket.

For example, to access a KV namespace from a Python Worker, you would declare the following in your Worker's Wrangler configuration file:

```jsonc
{
	"main": "./src/index.py",
	"kv_namespaces": [
		{
			"binding": "FOO
...
"id": "<YOUR_KV_NAMESPACE_ID>"
		}
	]
}
...
...and then call `.get()` on the binding object that is exposed on `env`:

```python
from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        await self.env.FOO.put("bar", "baz")
        bar = await self.env.FOO.get("bar")
        return Response(bar) # returns "baz"
...
, to interoperate with JavaScript APIs, you may ... to convert a ... object to JavaScript. Pyodide provides a `to_js` function to facilitate
...
We recommend using the `workers` module, which is provided by our `workers-runtime-sdk` package, to access JavaScript globals in a more Pythonic way. However, if you need to access JavaScript globals directly for any reason, you can import them from the `js` module.

---

Title: Write Cloudflare Workers in Python
URL: https://developers.cloudflare.com/workers/languages/python/
Published: 2026-09-17T00:00:00.000Z
Author: N/A
Highlights:
- Easy to install and fast-booting Packages, including FastAPI ↗, Langchain ↗, Pydantic ↗ and more.
- A robust foreign function interface (FFI) that lets you use JavaScript objects and functions directly from Python — including all Runtime APIs
- An ecosystem of services on the Workers Platform accessible via bindings, including: 

- State storage and databases like KV, D1, Durable Objects
- Access to Environment Variables, Secrets, and other Workers using Service Bindings
- AI capabilities with Workers AI, Vectorize
- File storage with R2
- Durable Workflows, Queues, and more
...
must add the `python_workers ... , while Python Workers are in open beta.
...
### The `pywrangler` CLI tool

To run a Python Worker locally, install packages, and deploy it to Cloudflare, you use pywrangler ↗, the CLI for Python Workers.

To set it up, first, ensure uv ↗ and Node ↗ are installed.

Then set up your development environment:

```
uvx --from workers-py pywrangler init
...
This will create a `pyproject.toml` file with `workers-py` as a development dependency. `pywrangler init` will create a wrangler config file. You can then run `pywrangler` with:

```
uv run pywrangler dev
...
To deploy a Python Worker to Cloudflare, run `pywrangler deploy`:

```
uv run pywrangler deploy
```

---

## Assistant (Build · Muse Spark 1.3 Free · 4.2s)

_Thinking:_



**Tool: websearch**

**Input:**
```json
{
  "contextMaxCharacters": 12000,
  "numResults": 8,
  "query": "python-workers-examples workers-ai env.AI.run python code",
  "type": "deep"
}
```

**Output:**
```
Title: python-workers-examples/09-workers-ai at main · cloudflare/python-workers-examples · GitHub
URL: https://github.com/cloudflare/python-workers-examples/tree/main/09-workers-ai
Published: 2024-03-28T19:51:35.000Z
Author: cloudflare
Highlights:
# Workers AI Example

## How to Run

First ensure that`uv` is installed: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run`uv run pywrangler dev` within this directory, it should use the config in`wrangler.jsonc` to run the example.

You can also run`uv run pywrangler deploy` to deploy the example.

---

Title: cloudflare/python-workers-examples
URL: https://github.com/cloudflare/python-workers-examples
Published: N/A
Author: N/A
Highlights:
- **`workers-ai/`** makes a call Workers AI to run inference on Cloudflare's Global Network.
...
- **`image-redraw/`** — an example ... combines FastAPI, ... 2, Queues, Workflows and Workers ... to redraw uploaded images.

---

Title: Workers Bindings · Cloudflare AI Gateway docs
URL: https://developers.cloudflare.com/ai-gateway/usage/worker-binding-methods/
Published: N/A
Author: N/A
Highlights:
## `env.AI.run()`

Runs an inference request through AI Gateway. Accepts Workers AI models (`@cf/` prefix) and third-party models (`{author}/{model}` format).

Workers AI model:

```
const resp = await env.AI.run(
	"@cf/moonshotai/kimi-k2.5",
	{
		prompt: "tell me a joke",
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
```
...
```
const resp = await env.AI.run(
	"@cf/moonshotai/kimi-k2.5",
	{
		prompt: "tell me a joke",
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
```
...
Third-party model:

```
const resp = await env.AI.run(
	"openai/gpt-4.1-mini",
	{
		messages: [{ role: "user", content: "tell me a joke" }],
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
...
```
const resp = await env.AI.run(
	"openai/gpt-4.1-mini",
	{
		messages: [{ role: "user", content: "tell me a joke" }],
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
...
The third argument to `env.AI.run()` accepts a `gateway` object with the following parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `string` | required | Name of your AI Gateway. Must be in the same account as your Worker. Use `"default"` to automatically create a gateway on the first authenticated request. Refer to Default gateway for details. |
| `skipCache` | `boolean` | `false` | Skip the cache for this request. |
| `cacheTtl` | `number` | — | Cache TTL in seconds. |
| `cacheKey` | `string` | — | Custom cache key for this request. |
| `collectLog` | `boolean` | — | Whether to collect logs for this request. |
| `metadata` | `object` | — | Custom metadata to attach to the log entry. |

---

Title: Code interpreter with Workers AI
URL: https://developers.cloudflare.com/sandbox/tutorials/workers-ai-code-interpreter/index.md
Published: N/A
Author: N/A
Highlights:
# Code interpreter with Workers
...
Build a powerful code interpreter that gives the gpt-oss model on Workers AI the ability to execute Python code using the Cloudflare Sandbox SDK.
...
A Cloudflare Worker that accepts natural language prompts, uses GPT-OSS to decide when Python code execution is needed, runs the code in isolated sandboxes, and returns results with AI-powered explanations.
...
```

// src/index.ts

import { getSandbox } from "@cloudflare/sandbox";

import { generateText, stepCountIs, tool } from "ai";

import { createWorkersAI } from "workers-ai-provider";

import { z } from "zod";
...
"@cf/openai/gpt ... 0b" as const;

async function handleAIRequest(input: string, env: Env): Promise<string> {

  const workersai = createWorkersAI({ binding: env.AI });

  const result = await generateText({

    model: workersai(MODEL),

    messages: [{ role: "user", content: input }],

    tools: {

      execute_python: tool({

        description: "Execute Python code and return the output",

        inputSchema: z.object({

          code: z.string().describe("The Python code to execute"),

        }),

        execute: async ({ code }) => {

          return executePythonCode(env, code);

        },

      }),

    },

    stopWhen: stepCountIs(5),

  });

  return result.text || "No response generated";

}

```
...
- Official packages: Uses `workers-ai-provider` instead of manual API calls
- Vercel AI SDK: Leverages `generateText()` and `tool()` for clean function calling
- No API keys: Uses native AI binding instead of environment variables
- Type safety: Full TypeScript support with proper typing
...
The template includes the proper Wrangler configuration:
...
```

{

  "name": "sandbox-code-interpreter-example",

  "main": "src/index.ts",

  // Set this to today's date

  "compatibility_date": "2026-06-08",

  "ai": {

    "binding": "AI"

  },

  "containers": [

    {

      "class_name": "Sandbox",

      "image": "./Dockerfile",

      "name": "sandbox",

      "max_instances": 1,

      "instance_type": "basic"

    }

  ],

  "durable_objects": {

    "bindings": [

      {

        "class_name": "Sandbox",

        "name": "Sandbox"

      }

    ]

  }

}

```
...
- AI binding: Enables direct access to Workers AI models
- Container setup: Configures sandbox container with Dockerfile
- Durable Objects: Provides persistent sandboxes with state management
...
```

# Simple calculation

curl -X POST http://localhost:8787/run \

  -H "Content-Type: application/json" \

  -d '{"input": "Calculate 5 factorial using Python"}'
...
1. User input: Send natural language prompts to the `/run` endpoint
2. AI decision: GPT-OSS receives the prompt with an `execute_python` tool available
3. Smart execution: Model decides whether Python code execution is needed
4. Sandbox isolation: Code runs in isolated Cloudflare Sandbox containers
5. AI explanation: Results are integrated back into the AI's response for final output
...
- Native Workers AI integration: Uses the official `workers-ai-provider` package for seamless integration
- Function calling: Leverages Vercel AI SDK for clean tool definitions and execution
- Secure execution: Runs Python code in isolated sandbox containers
- Intelligent responses: Combines AI reasoning with code execution results

---

Title: src/content/docs/sandbox/tutorials/workers-ai-code-interpreter.mdx
URL: https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/sandbox/tutorials/workers-ai-code-interpreter.mdx
Published: N/A
Author: N/A
Highlights:
Build a powerful code interpreter that gives the gpt-oss model on Workers AI the ability to execute Python code using the Cloudflare Sandbox SDK.
...
A Cloudflare Worker that accepts natural language prompts, uses GPT-OSS to decide when Python code execution is needed, runs the code in isolated sandboxes, and returns results with AI-powered explanations.
...
```typescript
// src/index.ts
import { getSandbox } from "@cloudflare/sandbox";
import { generateText, stepCountIs, tool } from "ai";
import { createWorkersAI } from "workers-ai-provider";
import { z } from "zod";

const MODEL = "@cf/openai/gpt-oss-120b" as const;

async function handleAIRequest(input: string, env: Env): Promise<string> {
	const workersai = createWorkersAI({ binding: env.AI });

	const result = await generateText({
		model: workersai(MODEL),
		messages: [{ role: "user", content: input }],
		tools: {
			execute_python: tool({
				description: "Execute Python code and return the output",
				inputSchema: z.object({
					code: z.string().describe("The Python code to execute"),
				}),
				execute: async ({ code }) => {
					return executePythonCode(env, code);
				},
			}),
		},
		stopWhen: stepCountIs(5),
	});

	return result.text || "No response generated";
}
```
...
- **Official packages**: Uses `workers-ai-provider` instead of manual API calls
- **Vercel AI SDK**: Leverages `generateText()` and `tool()` for clean function calling
- **No API keys**: Uses native AI binding instead of environment variables
- **Type safety**: Full TypeScript support with proper typing
...
The template includes the proper Wrangler configuration:

 
```json
{
  "name": "sandbox-code-interpreter-example",
  "main": "src/index.ts",
  "compatibility_date": "$today",
  "ai": {
    "binding": "AI"
  },
  "containers": [
    {
      "class_name": "Sandbox",
      "image": "./Dockerfile",
      "name": "sandbox",
      "max_instances": 1,
      "instance_type": "basic"
    }
  ],
  "durable_objects": {
    "bindings": [
      {
        "class_name": "Sandbox",
        "name": "Sandbox"
      }
    ]
  }
}
```
 

**Configuration highlights:**

- **AI binding**: Enables direct access to Workers AI models
- **Container setup**: Configures sandbox container with Dockerfile
- **Durable Objects**: Provides persistent sandboxes with state management
...
```sh
# ... calculation
curl -X POST http://localhost:8787/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Calculate 5 factorial using Python"}'
...
1. **User input**: Send natural language prompts to the `/run` endpoint
2. **AI decision**: GPT-OSS receives the prompt with an `execute_python` tool available
3. **Smart execution**: Model decides whether Python code execution is needed
4. **Sandbox isolation**: Code runs in isolated Cloudflare Sandbox containers
5. **AI explanation**: Results are integrated back into the AI's response for final output
...
- **Native Workers AI integration**: Uses the official `workers-ai-provider` package for seamless integration
- **Function calling**: Leverages Vercel AI SDK for clean tool definitions and execution
- **Secure execution**: Runs Python code in isolated sandbox containers
- **Intelligent responses**: Combines AI reasoning with code execution results

---

Title: Learn the basics of Python Workers · Cloudflare Workers docs
URL: https://developers.cloudflare.com/workers/languages/python/basics/
Published: N/A
Author: N/A
Highlights:
## The `env` Attribute

The `env` attribute on the `WorkerEntrypoint` can be used to access environment variables, secrets, and bindings.

For example, let us try setting and using an environment variable in a Python Worker. First, add the environment variable to your Worker's Wrangler configuration file:

```
{
	"$schema": "./node_modules/wrangler/config-schema.json",
	"name": "hello-python-worker",
	"main": "src/entry.py",
	"compatibility_flags": [
		"python_workers"
	],
	// Set this to today's date
	"compatibility_date": "2026-09-09",
	"vars": {
		"API_HOST": "example.com"
	}
}
...
"$schema" = "./node_modules/wrangler/config-schema.json"
name = "hello-python-worker"
main = "src/entry.py"
compatibility_flags = [ "python_workers" ]
# Set this to today's date
compatibility_date = "2026-09 ... 09"

[vars]
API_HOST = "example.com"
...
Then, you can access the `API_HOST` environment variable via the `env` parameter:

```
from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response(self.env.API_HOST)
...
The `workers-runtime-sdk` package provides the runtime SDK for Python Workers. This package is automatically installed and included in your worker when you use `pywrangler`, but you can also install it manually to take advantage of type hints and autocompletion in your IDE.
...
workers-runtime
...
Additionally, you can generate types based on your Worker configuration using `uv run pywrangler types`

This includes `Env` types based on your bindings, module rules, and runtime types based on the `compatibility_date` and `compatibility_flags` in your config file. See

---

Title: N/A
URL: https://cloudflare-sandbox-sdk.mintlify.app/examples/ai-code-execution
Published: N/A
Author: N/A
Highlights:
# AI code execution with Workers AI

> Give AI models the ability to execute Python code using the Sandbox SDK

Build an AI-powered code interpreter that gives language models the ability to execute Python code in isolated sandboxes. This example integrates Workers AI with the Sandbox SDK to create a secure code execution environment.
...
- Integrating Workers AI models with the Sandbox SDK
- Using the Vercel AI SDK for clean function calling
- Executing Python code in isolated containers
- Handling code execution results and errors
...
The user sends a natural language prompt to the `/run` endpoint requesting a calculation or code execution.
...
The GPT-OSS model receives the prompt along with an `execute_python` tool definition.
...
and generates the appropriate code.
...
The Python code executes in an isolated Cloudflare Sandbox container.
...
### Create the Python execution function

This function handles code execution in the sandbox and extracts results:

```typescript
...
{ getSandbox } from '@cloudflare/sandbox';

async function executePythonCode(env: Env, code: string): Promise<string> {
  const sandboxId = env.Sandbox.idFromName('default');
  const sandbox = getSandbox(env.Sandbox, sandboxId.toString().slice(0, 63));
  const pythonCtx = await sandbox.createCodeContext({ language: 'python' });
  const result = await sandbox.runCode(code, {
    context: pythonCtx
  });

  // Extract output from results (expressions)
  if (result.results?.length) {
    const outputs = result.results
      .map((r) => r.text || r.html || JSON.stringify(r))
      .filter(Boolean);
    if (outputs.length) return outputs.join('\n');
  }

  // Extract output from logs
  let output = '';
  if (result.logs?.stdout?.length) {
    output = result.logs.stdout.join('\n');
  }
  if (result.logs?.stderr?.length) {
    if (output) output += '\n';
    output += `Error: ${result.logs.stderr.join('\n')}`;
  }

  return result.error
    ? `Error: ${result.error}`
    : output || 'Code executed successfully';
}
...
### Set up the AI request handler

Integrate Workers AI with the Vercel AI SDK:

```typescript
import { generateText, stepCountIs, tool } from 'ai';
import { createWorkersAI } from 'workers-ai-provider';
import { z } from 'zod';

async function handleAIRequest(input: string, env: Env): Promise<string> {
  const workersai = createWorkersAI({ binding: env.AI });

  const result = await generateText({
    model: workersai('@cf/openai/gpt-oss-120b'),
    messages: [{ role: 'user', content: input }],
    tools: {
      execute_python: tool({
        description: 'Execute Python code and return the output',
        inputSchema: z.object({
          code: z.string().describe('The Python code to execute')
        }),
        execute: async ({ code }) => {
          return executePythonCode(env, code);
        }
      })
    },
    stopWhen: stepCountIs(5)
  });

  return result.text || 'No response generated';
}
...
### Create the Worker endpoint

Set up the API endpoint to handle requests:

```typescript
export { Sandbox } from '@cloudflare/sandbox';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname !== '/run' || request.method !== 'POST') {
      return new Response('Not Found', { status: 404 });
    }

    try {
      const { input } = await request.json<{ input?: string }>();

      if (!input) {
        return Response.json({ error: 'Missing input field' }, { status: 400 });
      }

      const output = await handleAIRequest(input, env);
      return Response.json({ output });
    } catch (error) {
      console.error('Request failed:', error);
      const message =
        error instanceof Error ? error.message : 'Internal Server Error';
      return Response.json({ error: message }, { status: 500 });
    }
  }
} satisfies ExportedHandler<Env>;
...
## Example usage

Test the code interpreter with various prompts:

```bash
# Simple calculation
curl -X POST http://localhost:8787/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Calculate 5 factorial using Python"}'

# Execute specific code
curl -X POST http://localhost:8787/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Execute this Python: print(sum(range(1, 101)))"}'

# Complex operations
curl -X POST http://localhost:8787/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Use Python to find all prime numbers under 20"}'
...
```bash
npm install @cloudflare/sandbox ai workers-
...
- Workers AI Integration: Uses the `@cf/openai/gpt-oss-120b` model via the workers-ai-provider package
- Vercel AI SDK: Leverages `generateText()` and `tool()` for clean function calling patterns
- Sandbox Execution: Python code runs in isolated Cloudflare Sandbox containers
- Result Handling: Extracts outputs from both expression results and stdout/stderr logs
- Error Handling: Properly surfaces execution errors to the AI model

---

Title: Write Cloudflare Workers in Python
URL: https://developers.cloudflare.com/workers/languages/python/
Published: 2026-09-17T00:00:00.000Z
Author: N/A
Highlights:
, Langchain ... , Pydantic
...
foreign function interface
...
- State storage and databases like KV, D1, Durable Objects
- Access to Environment Variables, Secrets, and other Workers using Service Bindings
- AI capabilities with Workers AI, Vectorize
- File storage with R2
- Durable Workflows, Queues, and more
...
To run a Python Worker locally, install packages, and deploy it to Cloudflare, you use pywrangler ↗, the CLI for Python Workers.
...
This will create a `pyproject.toml` file with `workers-py` as a development dependency. `pywrangler init` will create a wrangler config file. You can then run `pywrangler` with:
...
you initialize a new Python Worker project and select from ... of many templates:
...
Or you can clone the examples repository to explore more options:

```
git clone https://github.com/cloudflare/python-workers-examples
cd python-workers-examples/hello
```

**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://github.com/cloudflare/python-workers-examples/tree/main/examples/workers-ai"
}
```

**Error:**
```
StatusCode: non 2xx status code (404 GET https://github.com/cloudflare/python-workers-examples/tree/main/examples/workers-ai)
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.2s)

**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://github.com/cloudflare/python-workers-examples/tree/main/09-workers-ai"
}
```

**Error:**
```
StatusCode: non 2xx status code (404 GET https://github.com/cloudflare/python-workers-examples/tree/main/09-workers-ai)
```

**Tool: websearch**

**Input:**
```json
{
  "contextMaxCharacters": 15000,
  "numResults": 6,
  "query": "\"await env.AI.run\" python worker pyodide to_js Workers AI llama",
  "type": "deep"
}
```

**Output:**
```
Title: Workers Bindings · Cloudflare Workers AI docs
URL: https://developers.cloudflare.com/workers-ai/configuration/bindings/
Published: N/A
Author: N/A
Highlights:
To use Workers AI with Workers, you must create a Workers AI binding. Bindings allow your Workers to interact with resources, like Workers AI, on the Cloudflare Developer Platform. You create bindings on the Cloudflare dashboard or by updating your Wrangler file.
...
### async env.AI.run()

`async env.AI.run()` runs a model. Takes a model as the first parameter, and an object as the second parameter.

```
const answer = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
    prompt: "What is the origin of the phrase 'Hello, World'"
});
...
- `model` `string` required

- The model to run.
...
- `stream``boolean` optional

- Returns a stream of results as they are available.

```
const answer = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
    prompt: "What is the origin of the phrase 'Hello, World'",
    stream: true
});

return new Response(answer, {
    headers: { "content-type": "text/event-stream" }
});
```

---

Title: Python Workers are now generally available
URL: https://blog.cloudflare.com/python-workers-ga/
Published: 2026-09-21T18:23:46.734Z
Author: N/A
Highlights:
What does GA mean? It means Python is now a first-class, fully supported language on the Cloudflare Developer Platform. You can bring the Python code, libraries, and design patterns you already know and connect them seamlessly to Workers AI, R2, D1, Hyperdrive, Durable Objects, Queues, Workflows, and the rest of the Cloudflare platform. You can also run popular Python frameworks like FastAPI, Django, and Flask inside Python Workers. You can even create a Python Worker inside another Worker using Dynamic Workers.
...
@app.get("/")
async def root(request: Request):
    env = request.scope["env"]
    return await env.AI.run(
        "@cf/openai/gpt-oss-120b",
        {
            "instructions": "You are a friendly assistant.",
            "input": "What is the origin of the phrase Hello, World?",
        },
    )
...
Bringing Python to Cloudflare Workers was a natural choice. Because Workers has supported WebAssembly since 2018, it gave us the perfect environment to run a Wasm-compiled Python interpreter. By using Pyodide, we were able to quickly support a wide range of Python applications in Cloudflare Workers.
...
Python Workers now natively support Cloudflare Developer Platform bindings. Previously, using these Cloudflare bindings in Python Workers required converting Python objects into TypeScript objects explicitly at the RPC boundary. For example, sending a Python dictionary into a Cloudflare Queue required the following glue code to work:

```
from pyodide.ffi import to_js
import js

self.env.QUEUE.send(to_js({"key": "value"}, dict_converter=js.Object.fromEntries))

```

This required Python developers to keep the JavaScript environment and code in mind while writing Python Workers, and it was a common source of error for both humans and AI agents. To address this, we have encapsulated the entire type conversion process within the Workers runtime and the Python SDK. This allows you to utilize all Cloudflare bindings in a Pythonic way without writing a single line of JavaScript code, making the following just work:
...
The large ecosystem of data science and machine learning packages makes Python the natural choice for building intelligent agents and AI pipelines. But bringing these to Python Workers historically presented a challenge: libraries such as `openai` and `langchain` rely on HTTP clients like `requests` or `httpx` to communicate with external APIs. However, because of missing low-level socket operations support in Python Workers, these HTTP clients didn’t work properly.

To solve this, we contributed upstream to ensure these HTTP clients can route requests directly through the JavaScript `fetch` API in WebAssembly environments. Combined with our new support for low-level socket operations as explained in the previous section, this makes the entire networking stack work seamlessly inside Python Workers.

As a result, you can now run AI libraries like `openai`, `langchain`, and `mcp` natively in Python Workers. You can also combine them with Workers AI to run serverless inference on GPUs in Cloudflare’s network, or proxy requests through Cloudflare AI Gateway.

The example below shows a way to run Worker AI models in langchain, using the langchain-cloudflare package:

```
from langchain_cloudflare import ChatCloudflareWorkersAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from workers import Response, WorkerEntrypoint

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        prompt = PromptTemplate.from_template(
            "In one sentence, describe a great day in the life of an {profession}."
        )
        llm = ChatCloudflareWorkersAI(
            model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            binding=self.env.AI,
            max_tokens=64,
        )
        chain = prompt | llm | StrOutputParser()

        result = await chain.ainvoke({"profession": "electrician"})
        return Response.json({"result": result})

```

---

Title: Python worker can't access env.AI methods like run after binding · Issue #1992 · cloudflare/workerd
URL: https://github.com/cloudflare/workerd/issues/1992
Published: 2024-04-08T20:37:36.000Z
Author: neeravkumar
Highlights:
## Python worker can't access env.AI methods like run after binding
...
Can't create a python worker that can access the AI bindings

````py
from js import Response

async def on_fetch(request, env):
    simple = "{'prompt': 'Tell me a random quote'}"
    response = await env.AI.run("@cf/meta/llama-2-7b-chat-int8", simple)
    return Response.new(response)
```
...
```py
Traceback (most recent call last):
  File \"/session/metadata/entry.py\", line 5, in on_fetch
    response = await env.AI.run(\"@cf/meta/llama-2-7b-chat-int8\", simple)
                     ^^^^^^^^^^
AttributeError: run
```
...
> For context, in JavaScript [you would write](https://developers.cloudflare.com/workers-ai/get-started/workers-wrangler/#4-run-an-inference-task-in-your-worker):
> 
> ```js
> import { Ai } from '@cloudflare/ai'
> 
> export interface Env {
>   // If you set another name in wrangler.toml as the value for 'binding',
>   // replace "AI" with the variable name you defined.
>   AI: any;
> }
> 
> async function fetch(request: Request, env: Env) {
>   const ai = new Ai(env.AI);
>   const response = await ai.run('@cf/meta/llama-2-7b-chat-int8', {
>       prompt: "What is the origin of the phrase Hello, World"
>     }
>   );
> }
> ```
> 
> So the `run` method is on the `Ai` wrapper and not on `env.AI` itself. We need some plan for how to allow Python workers to access equivalent functionality.
...
> So is there an answer on how we can all env.AI from python ?
...
> We've got a test for it here: https://github.com/cloudflare/workerd/blob/main/src/cloudflare/internal/test/ai/ai-api-test.py. So something close @neeravkumar's code should work these days. Let us know if you run into any issues.

---

Title: Workers Bindings · Cloudflare AI Gateway docs
URL: https://developers.cloudflare.com/ai-gateway/usage/worker-binding-methods/
Published: N/A
Author: N/A
Highlights:
The AI binding (`env.AI`) lets you call AI models and access AI Gateway features directly from your Worker.
...
binding is accessible ... your Worker code as `env
...
## `env.AI.run()`

Runs an inference request through AI Gateway. Accepts Workers AI models (`@cf/` prefix) and third-party models (`{author}/{model}` format).

Workers AI model:

```
const resp = await env.AI.run(
	"@cf/moonshotai/kimi-k2.5",
	{
		prompt: "tell me a joke",
	},
	{
		gateway: {
			id: "default", // or use a specific gateway name
		},
	},
);
```
...
gateway name
		},
...
party models require an AI Gateway and use Unified Billing. Cloudflare manages the provider credentials and deducts credits from your account. You do not need to supply your own API keys.
...
request falls through ... ig-byok
...
### Gateway options

The third argument to `env.AI.run()` accepts a `gateway` object with the following parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `string` | required | Name of your AI Gateway. Must be in the same account as your Worker. Use `"default"` to automatically create a gateway on the first authenticated request. Refer to Default gateway for details. |
| `skipCache` | `boolean` | `false` | Skip the cache for this request. |
| `cacheTtl` | `number` | — | Cache TTL in seconds. |
| `cacheKey` | `string` | — | Custom cache key for this request. |
| `collectLog` | `boolean` | — | Whether to collect logs for this request. |
| `metadata` | `object` | — | Custom metadata to attach to the log entry. |

---

Title: Set up Workers AI with AI Gateway · Cloudflare AI Gateway docs
URL: https://developers.cloudflare.com/ai-gateway/integrations/aig-workers-ai-binding/
Published: N/A
Author: N/A
Highlights:
2. Connect your Worker to Workers AI

You must create an AI binding for your Worker to connect to Workers AI. Bindings allow your Workers to interact with resources, like Workers AI, on the Cloudflare Developer Platform.

To bind Workers AI to your Worker, add the following to the end of your Wrangler configuration file:

```
{
	"ai": {
		"binding": "AI",
	},
}
...
```
[ai]
binding = "AI"
...
Your binding is available in your Worker code on `env.AI`.

You can use `"default"` as the gateway ID in the next step. AI Gateway automatically creates a default gateway on the first authenticated request. Alternatively, you can create a gateway manually and use its ID.

## 3. Run an inference task containing AI Gateway in your Worker

You are now ready to run an inference task in your Worker. In this case, you will use an LLM, `llama-3.1-8b-instruct-fast`, to answer a question.

Update the `index.ts` file in your `hello-ai` application directory with the following code:
...
```
export interface Env {
	// If you set another name in the [Wrangler configuration file](/workers/wrangler/configuration/) as the value for 'binding',
	// replace "AI" with the variable name you defined.
	AI: Ai;
}

export default {
	async fetch(request, env): Promise<Response> {
		// Specify the gateway label and other options here
		const response = await env.AI.run(
			"@cf/meta/llama-3.1-8b-instruct-fast",
			{
				prompt: "What is the origin of the phrase Hello, World",
			},
			{
				gateway: {
					id: "default", // Uses the default gateway, or replace with your gateway ID
					skipCache: true, // Optional: Skip cache if needed
				},
			},
		);

		// Return the AI response as a JSON object
		return new Response(JSON.stringify(response), {
			headers: { "Content-Type": "application/json" },
		});
	},
} satisfies ExportedHandler<Env>;
```
...
Up to this point, you have created an AI binding for your Worker and configured your Worker to be able to execute the Llama 3.1 model. You can now test your project locally before you deploy globally.
...
By completing this tutorial, you have created a Worker, connected it to Workers AI through an AI Gateway binding, and successfully ran an inference task using the Llama 3.1 model.

---

Title: feat(types): add overload-based AI.run() with gateway fallback and gemma-4 · b2ba62c · cloudflare/workerd
URL: https://github.com/cloudflare/workerd/commit/b2ba62c2e6659b84ec752692ffa5c63192fe24e4
Published: 2026-04-09T00:00:00.000Z
Author: samscott89
Highlights:
# b2ba62c feat(types): add overload-based AI.run() with gateway fallback and gemma-4
...
feat(types): add overload-based AI.run() with gateway fallback and gemma-4

Add overload-based run() signatures for better type inference:
- Batch request (queueRequest: true) -> AsyncResponse
- Raw response (returnRawResponse: true) -> Response
- WebSocket (websocket: true) -> Response
- Streaming (stream: true in inputs) -> ReadableStream
- Normal -> model-specific output type
- Unknown model (gateway fallback) -> Record<string, unknown>

The gateway fallback allows AI Gateway models (e.g. 'google/nano-banana')
to be called without type errors while preserving full type safety for
known Cloudflare AI models.

Also adds gemma-4-26b-a4b-it model types and type-check tests.
```

---

## Assistant (Build · Muse Spark 1.3 Free · 9.7s)

_Thinking:_

Checking Workers AI Python binding usage and chat message format for gpt-oss and llama models.

**Tool: websearch**

**Input:**
```json
{
  "contextMaxCharacters": 15000,
  "numResults": 6,
  "query": "Cloudflare Workers AI llama-3.1-8b-instruct messages input response format response field",
  "type": "deep"
}
```

**Output:**
```
Title: llama-3.1-8b-instruct (Meta) · Cloudflare AI docs · Cloudflare Workers AI docs
URL: https://developers.cloudflare.com/workers-ai/models/llama-3.1-8b-instruct/
Published: N/A
Author: N/A
Highlights:
[
      { role ... "You are a friendly assistant"
...
];

    const ... = await env.AI ... ("@cf/meta/llama-3.1-8b-instruct
...
messages,
...
,
    });
...
content-type": ... -stream" },
...
},
} satisfies
...
response = requests.post(
  f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct",
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    json={
      "messages": [
        {"role": "system", "content": "You are a friendly assistant"},
        {"role": "user", "content": prompt}
      ]
    }
)
...
`string` required minLength: 1 The input text prompt for the model to generate a response.
...
▶ response_format{} `object`

`boolean` default: false If true, a chat template is not applied and you must adhere to the specific model's expected formatting.
...
Synchronous — Send a request and receive a complete response

Filter parameters...

response `string` The generated text response from the model

---

Title: N/A
URL: https://developers.cloudflare.com/workers-ai/features/json-mode/index.md
Published: N/A
Author: N/A
Highlights:
Workers AI supports JSON Mode, enabling applications to request a structured output response when interacting with AI models.
...
JSON Mode is compatible with OpenAI’s implementation; to enable add the `response_format` property to the request object using the following convention:

```json
{
  response_format: {
    title: "JSON Mode",
    type: "object",
    properties: {
      type: {
        type: "string",
        enum: ["json_object", "json_schema"],
      },
      json_schema: {},
    }
  }
}
...
Where `json_schema` must be a valid JSON Schema ↗ declaration.
...
When using JSON Format, pass the schema as in the example below as part of the request you send to the LLM.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Extract data about a country."
    },
    {
      "role": "user",
      "content": "Tell me about India."
    }
  ],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "capital": {
          "type": "string"
        },
        "languages": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "name",
        "capital",
        "languages"
      ]
    }
  }
}

```

The LLM will follow the schema, and return a response such as below:

```json
{
  "response": {
    "name": "India",
    "capital": "New Delhi",
    "languages": [
      "Hindi",
      "English",
      "Bengali",
      "Telugu",
      "Marathi",
      "Tamil",
      "Gujarati",
      "Urdu",
      "Kannada",
      "Odia",
      "Malayalam",
      "Punjabi",
      "Sanskrit"
    ]
  }
}

```
...
This is the list of models that now support
...
- @cf/meta/llama-3.1-8b-instruct-fast
- @cf/meta/llama-3.1-70b-instruct
- @cf/meta/llama-3.3-70b-instruct-fp8-fast
- @cf/meta/llama-3-8b-instruct
- @cf/meta/llama-3.1-8b-instruct
- @cf/meta/llama-3.2-11b-vision-instruct
- @hf/nousresearch/hermes-2-pro-mistral-7b
- @hf/thebloke/deepseek-coder-6.7b-instruct-awq
- @cf/deepseek-ai/deepseek-r1-distill-qwen-32b
...
Note that Workers AI can't guarantee that the model responds according to the requested JSON Schema. Depending on the complexity of the task and adequacy of the JSON Schema, the model may not be able to satisfy the request in extreme situations. If that's the case, then an error `JSON Mode couldn't be met` is returned and must be handled.

---

Title: skills/cloudflare/references/workers-ai/README.md
URL: https://github.com/cloudflare/skills/blob/main/skills/cloudflare/references/workers-ai/README.md
Published: N/A
Author: N/A
Highlights:
export default {
  async fetch(request: Request, env: Env) {
    const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
      messages: [{ role: 'user', content: 'What is Cloudflare?' }]
    });
    return Response.json(response);
  }
};
```
...
```bash
curl https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/ai/run/@cf/meta/llama-3.1-8b-instruct \
  -H "Authorization: Bearer <API_TOKEN>" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
...
// Function calling
const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
  messages: [{ role: 'user', content: 'What is the weather?' }],
  tools: [{
    type: 'function',
    function: { name: 'getWeather', parameters: { ... } }
  }]
});
```

---

Title: llama-3.1-8b-instruct-fast (Meta) · Cloudflare AI docs · Cloudflare Workers AI docs
URL: https://developers.cloudflare.com/workers-ai/models/llama-3.1-8b-instruct-fast/
Published: N/A
Author: N/A
Highlights:
export default {
  async fetch(request, env): Promise<Response> {

    const messages = [
      { role: "system", content: "You are a friendly assistant" },
      {
        role: "user",
        content: "What is the origin of the phrase Hello, World",
      },
    ];

    const stream = await env.AI.run("@cf/meta/llama-3.1-8b-instruct-fast", {
      messages,
      stream: true,
    });

    return new Response(stream, {
      headers: { "content-type": "text/event-stream" },
    });
  },
} satisfies ExportedHandler<Env>;
...
export default {
  async fetch ... request, env): Promise<Response> {

    const messages = [
      { role: "system", content: "You are a friendly assistant" },
      {
        role: "user",
        content: "What is the origin of the phrase Hello, World",
      },
    ];
    const response = await env.AI.run("@cf/meta/llama-3 ... 1-8b-instruct-fast", { messages });

    return Response.json(response);
  },
} satisfies ExportedHandler<Env>;
...
response = requests.post(
  f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.1-8b-instruct-fast",
    headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
    json={
      "messages": [
        {"role": "system", "content": "You are a friendly assistant"},
        {"role": "user", "content": prompt}
      ]
    }
)
result = response.json()
print(result)
...
`string` required maxLength: 131072 minLength: 1 The input text prompt for the model to generate a response.
...
Synchronous — Send a request and receive a complete response

Filter parameters...

response `string` The generated text response from the model
...
Streaming — Send a request with `stream: true` and receive server-sent events
...
contentType `text/event-stream`

format `binary`

type `string`

---

Title: Workers AI Changelog
URL: https://developers.cloudflare.com/changelog/product/workers-ai/
Published: N/A
Author: N/A
Highlights:
- `@cf/moonshotai/kimi-k2.5` --> `@cf/moonshotai/kimi-k2.6`
- `@hf/meta-llama/meta-llama-3-8b-instruct`
- `@cf/meta/llama-3-8b-instruct`
- `@cf/meta/llama-3-8b-instruct-awq`
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/meta/llama-3.1-8b-instruct-awq`
- `@cf/meta/llama-3.1-70b-instruct`
- `@cf/meta/llama-2-7b-chat-int8`
- `@cf/meta/llama-2-7b-chat-fp16`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@hf/mistral/mistral-7b-instruct-v0.2`
- `@hf/google/gemma-7b-it`
- `@cf/google/gemma-3-12b-it`
- `@hf/nousresearch/hermes-2-pro-mistral-7b`
- `@cf/microsoft/phi-2`
- `@cf/defog/sqlcoder-7b-2`
- `@cf/unum/uform-gen2-qwen-500m`
- `@cf/facebook/bart-large-cnn`
...
- `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- `@cf/meta/llama-3.1-8b-instruct-fast`
- `@cf/google/gemma-7b-it-lora`
- `@cf/google/gemma-2b-it-lora`
- `@cf/mistral/mistral-7b-instruct-v0.2-lora`
- `@cf/meta-llama/llama-2-7b-chat-hf-lora`

---

Title: N/A
URL: https://developers.cloudflare.com/workers-ai/features/prompting/index.md
Published: N/A
Author: N/A
Highlights:
Scoped prompts are a list of messages. Each message defines two keys: the role and the content.
...
- system - System messages define the AI's personality. You can use them to set rules and how you expect the AI to behave.
- user - User messages are where you actually query the AI by providing a question or a conversation.
- assistant - Assistant messages hint to the AI about the desired output format. Not all models support this role.
...
Here's an input example of a scoped prompt using system and user roles:

```js
{
  messages: [
    { role: "system", content: "you are a very funny comedian and you like emojis" },
    { role: "user", content: "tell me a joke about cloudflare" },
  ],
};
...
of a chat session using multiple iterations between the user and the assistant.

```js
{
  messages: [
    { role: "system", content: "you are a professional computer science assistant" },
    { role: "user", content: "what is WASM?" },
    { role: "assistant", content: "WASM (WebAssembly) is a binary instruction format that is designed to be a platform-agnostic" },
    { role: "user", content: "does Python compile to WASM?" },
    { role: "assistant", content: "No, Python does not directly compile to WebAssembly" },
    { role: "user", content: "what about Rust?" },
  ],
};
...
Note that different LLMs are trained with different templates for different use cases. While Workers AI tries its best to abstract the specifics of each LLM template from the developer through a unified API, you should always refer to the model documentation for details. For example, instruct models like Codellama are fine-tuned to respond to a user-provided instruction, while chat models expect fragments of dialogs as input.
...
You can use unscoped prompts to send a single question to the model without worrying about providing any context. Workers AI will automatically convert your `prompt` input to a reasonable default scoped prompt internally so that you get the best possible prediction.
...
You can also use unscoped prompts to construct the model chat template manually. In this case, you can use the raw parameter. Here's an input example of a Mistral ↗ chat template prompt:

```js
{
  prompt: "<s>[INST]comedian[/INST]</s>
[INST]tell me a joke about cloudflare[/INST]",
  raw: true
};
```

**Tool: websearch**

**Input:**
```json
{
  "contextMaxCharacters": 12000,
  "numResults": 6,
  "query": "Cloudflare Workers AI gpt-oss-120b instructions input output_type response format",
  "type": "deep"
}
```

**Output:**
```
Title: gpt-oss-120b (OpenAI) · Cloudflare AI docs · Cloudflare Workers AI docs
URL: https://developers.cloudflare.com/workers-ai/models/gpt-oss-120b/
Published: N/A
Author: N/A
Highlights:
Synchronous — Send a request and receive a complete response
...
Simple text input for single-turn interactions
...
Structured conversation format with roles (user, assistant, system)
...
`string` required minLength: 1 The input text prompt for the model to generate a response.
...
▶ response_format{} `object`
...
`boolean` default: false If true, a chat template is not applied and you must adhere to the specific model's expected formatting.
...
response `string` The generated text response from the model
...
— Send a request with `stream: true` and receive server-sent events
...
▶ response_format{} `object`
...
type `string`
...
contentType `text/event-stream`
...
## API Sche ... (Raw)

---

Title: 9e079ed [Workers AI] Add detailed output schemas for gpt-oss-20b and gpt-oss-120b models (#30119)
URL: https://github.com/cloudflare/cloudflare-docs/commit/9e079edd2afcfb1180a04564eb8e74080f086567
Published: N/A
Author: N/A
Highlights:
# 9e079ed [Workers AI] Add detailed output schemas for gpt-oss-20b and gpt-oss-120b models (#30119)
...
Previously, the output schema for GPT-OSS models was a generic object/string
definition that didn't provide any useful information about what the models
actually return.

This commit adds comprehensive output schema documentation for all three
API formats supported by these models:

- Prompt_Output: Legacy Workers AI format with response, usage, and tool_calls
- Messages_Output: OpenAI Chat Completions API format with choices array
- Responses_Output: OpenAI Responses API format with structured output items
- Responses_Async_Output: Async Batch API format with results array
- Stream_Output: Server-Sent Events for streaming responses

Each output format now includes detailed property definitions, descriptions,
and type information to help developers understand the exact response structure.
...
| File | Status | + | - |
| --- | --- | --- | --- |
| src/content/workers-ai-models/gpt-oss-120b.json | modified | 389 | 3 |
| src/content/workers-ai-models/gpt-oss-20b.json | modified | 389 | 3 |

---

Title: N/A
URL: https://blog.cloudflare.com/openai-gpt-oss-on-workers-ai/
Published: 2025-08-05T00:00:00.000Z
Author: N/A
Highlights:
OpenAI has just announced their latest open-weight models — and we are excited to share that we are working with them as a Day 0 launch partner to make these models available in Cloudflare's Workers AI. Cloudflare developers can now access OpenAI's first open model, leveraging these powerful new capabilities on our platform. The new models are available starting today at `@cf/openai/gpt-oss-120b` and `@cf/openai/gpt-oss-20b`.
...
We’re landing these new models with a few tweaks: supporting the new Responses API format as well as the historical Chat Completions API format (coming soon). The Responses API format is recommended by OpenAI to interact with their models, and we’re excited to support that on Workers AI.
...
- Workers Binding, it will accept/return Responses API – `env.AI.run(“@cf/openai/gpt-oss-120b”)`
- REST API on /run endpoint, it will accept/return Responses API – `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/run/@cf/openai/gpt-oss-120b`
- REST API on new /responses endpoint, it will accept/return Responses API – `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/responses`
- REST API for OpenAI Compatible endpoint, it will return Chat Completions (coming soon)– `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/chat/completions`

```
curl https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
  -d '{
    "model": "@cf/openai/gpt-oss-120b",
    "reasoning": {"effort": "medium"},
    "input": [
      {
        "role": "user",
        "content": "What are the benefits of open-source models?"
      }
    ]
  }'

```

---

Title: Types missing for new AI models `gpt-oss-120b`, `gpt-oss-20b`
URL: https://github.com/cloudflare/workerd/issues/5080
Published: N/A
Author: N/A
Highlights:
This model is missing from the input types:

```ts
await env.AI.run('@cf/openai/gpt-oss-120b', {
	instructions: 'some prompt'
	input: 'some input',
	max_tokens: 10240,
})
```

`Argument of type '"@cf/openai/gpt-oss-120b"' is not assignable to parameter of type 'keyof AiModels'.ts(2345)`

And I've not found any output type that matches the output correctly either. It's very different from `AiTextGenerationOutput`. This isn't helped when https://developers.cloudflare.com/workers-ai/models/gpt-oss-120b/ doesn't document this type either.
...
> It seems like an update here landed as per https://github.com/cloudflare/workerd/pull/5111, but as per my comment at https://github.com/cloudflare/workerd/pull/5111#issuecomment-3304247714, the output types for these models are not quite accurate and now throw errors like this:
> ```ts
> const response = await context.env.AI.run('@cf/openai/gpt-oss-120b', {
> instructions: 'some prompt',
> input: 'some input',
> max_tokens: 10240,
> });
> 
> const results = response?.output?.find?.(item => item.type === 'message');
> ```
> 
> ```
> Property 'output' does not exist on type 'Ai_Cf_Openai_Gpt_Oss_120B_Output'.
> Property 'output' does not exist on type '{}'.
> ```
> cc @thatsKevinJain
...
> Hey @robzlabz the types package has been updated for the gpt-oss models: https://github.com/cloudflare/workerd/pull/5434
> 
> You can update the "@cloudflare/workers-types" to the latest version.

---

Title: N/A
URL: https://developers.cloudflare.com/changelog/post/2025-08-05-openai-open-models/
Published: 2025-08-05T00:00:00.000Z
Author: N/A
Highlights:
We're thrilled to be a Day 0 partner with OpenAI ↗ to bring their latest open models ↗ to Workers AI, including support for Responses API, Code Interpreter, and Web Search (coming soon).

Get started with the new models at `@cf/openai/gpt-oss-120b` and `@cf/openai/gpt-oss-20b`. Check out the blog ↗ for more details about the new models, and the `gpt-oss-120b` and `gpt-oss-20b` model pages for more information about pricing and context windows.

#### Responses API

If you call the model through:

- Workers Binding, it will accept/return Responses API – `env.AI.run(“@cf/openai/gpt-oss-120b”)`
- REST API on `/run` endpoint, it will accept/return Responses API – `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/run/@cf/openai/gpt-oss-120b`
- REST API on new `/responses` endpoint, it will accept/return Responses API – `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/responses`
- REST API for OpenAI Compatible endpoint, it will return Chat Completions (coming soon) – `https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/chat/completions`

```
curl https://api.cloudflare.com/client/v4/accounts/<account_id>/ai/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
  -d '{
    "model": "@cf/openai/gpt-oss-120b",
    "reasoning": {"effort": "medium"},
    "input": [
      {
        "role": "user",
        "content": "What are the benefits of open-source models?"
      }
    ]
  }'

```

---

Title: Prompting · Cloudflare Workers AI docs
URL: https://developers.cloudflare.com/workers-ai/features/prompting/
Published: N/A
Author: N/A
Highlights:
We recommend using unsc ... inference with LoRA.
...
This is the recommended method. With scoped prompts, Workers AI takes the burden of knowing and using different chat templates for different models and provides a unified interface to developers when building prompts and creating text generation tasks.

Scoped prompts are a list of messages. Each message defines two keys: the role and the content.
...
- system - System messages define the AI's personality. You can use them to set rules and how you expect the AI to behave.
- user - User messages are where you actually query the AI by providing a question or a conversation.
- assistant - Assistant messages hint to the AI about the desired output format. Not all models support this role.
...
Note that different LLMs are trained with different templates for different use cases. While Workers AI tries its best to abstract the specifics of each LLM template from the developer through a unified API, you should always refer to the model documentation for details. For example, instruct models like Codellama are fine-tuned to respond to a user-provided instruction, while chat models expect fragments of dialogs as input.
...
You can use unscoped prompts to send a single question to the model without worrying about providing any context. Workers AI will automatically convert your `prompt` input to a reasonable default scoped prompt internally so that you get the best possible prediction.
...
You can also use unscoped prompts to construct the model chat template manually. In this case, you can use the raw parameter. Here's an input example of a Mistral ↗ chat template prompt:

```
{
  prompt: "<s>[INST]comedian[/INST]</s>
[INST]tell me a joke about cloudflare[/INST]",
  raw: true
};
```

---

## Assistant (Build · Muse Spark 1.3 Free · 7.7s)

_Thinking:_

Evaluating model response formats and choosing a simple text-based JSON approach for structured output.

**Tool: webfetch**

**Input:**
```json
{
  "format": "text",
  "url": "https://raw.githubusercontent.com/cloudflare/workerd/main/src/cloudflare/internal/test/ai/ai-api-test.py"
}
```

**Output:**
```
# Copyright (c) 2024 Cloudflare, Inc.
# Licensed under the Apache 2.0 license found in the LICENSE file or at:
#     https://opensource.org/licenses/Apache-2.0


async def test(context, env):
    resp = await env.ai.run("testModel", {"prompt": "test"})
    assert resp.response == "model response"

    # Test request id is present
    assert env.ai.lastRequestId == "3a1983d7-1ddd-453a-ab75-c4358c91b582"

```

**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://developers.cloudflare.com/workers-ai/models/llama-3.1-8b-instruct/"
}
```

**Error:**
```
StatusCode: non 2xx status code (404 GET https://developers.cloudflare.com/workers-ai/models/llama-3.1-8b-instruct/)
```

---

## Assistant (Build · Muse Spark 1.3 Free · 19.2s)

_Thinking:_

Evaluating Python binding response handling for dict vs attribute access and Pyodide JsProxy compatibility.

_Thinking:_

Designing helpers to build prompts, parse JSON, and surface Workers AI and parse errors.

_Thinking:_



**Tool: bash**

**Input:**
```json
{
  "command": "ls tests/ && python3 -m pytest tests/ -q 2>&1 | tail -5; ls .venv/bin/ | head -20",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
__pycache__
test_repository.py
/home/akhileshmt/Documents/Fun/wtf-error/.venv-workers/bin/python3: No module named pytest
activate
activate.bat
activate.csh
activate.fish
activate.nu
activate.ps1
activate_this.py
deactivate.bat
fastapi
idna
markdown-it
pydoc.bat
pygmentize
pyodide
pyrefly
python
python3
python3.13
pywrangler
uvicorn

```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.2s)

**Tool: bash**

**Input:**
```json
{
  "command": "python3 -m unittest discover -s tests -v 2>&1 | tail -10",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
test_create_finding_inserts_all_fields (test_repository.RepositoryMessagesFindingsTest.test_create_finding_inserts_all_fields) ... ok
test_create_message_inserts_all_fields (test_repository.RepositoryMessagesFindingsTest.test_create_message_inserts_all_fields) ... ok
test_errors_are_not_swallowed (test_repository.RepositoryMessagesFindingsTest.test_errors_are_not_swallowed) ... ok
test_list_findings_orders_and_isolates_incident (test_repository.RepositoryMessagesFindingsTest.test_list_findings_orders_and_isolates_incident) ... ok
test_list_messages_orders_for_conversation_history (test_repository.RepositoryMessagesFindingsTest.test_list_messages_orders_for_conversation_history) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.023s

OK

```

---

## Assistant (Build · Muse Spark 1.3 Free · 11.5s)

_Thinking:_

Designing investigation orchestration with message building, parsing, and async model call functions.

_Thinking:_

Adding parsing with fence stripping and schema checks plus async model call with response extraction.

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "Create src/investigation.py orchestration service",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Add tests/test_investigation.py with fakes",
      "status": "pending",
      "priority": "high"
    },
    {
      "content": "Run test suite and verify",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "Create src/investigation.py orchestration service",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "content": "Add tests/test_investigation.py with fakes",
    "status": "pending",
    "priority": "high"
  },
  {
    "content": "Run test suite and verify",
    "status": "pending",
    "priority": "high"
  }
]
```

---

## Assistant (Build · Muse Spark 1.3 Free · 17.8s)

**Tool: write**

**Input:**
```json
{
  "content": "\"\"\"Orchestration-only incident investigation service (first version).\n\nPipeline::\n\n    incident + history\n            ↓\n    build context\n            ↓\n    Workers AI (one model call)\n            ↓\n    structured investigation result\n\nDeliberately out of scope here: API routes, raw SQL, persistence of the\nAI response, retries, loops, tool calling, agents, background jobs, RAG,\nembeddings. Workers AI errors are allowed to propagate to the caller.\n\nWorkers AI call shape\n---------------------\nThe AI-specific code lives only in :func:`run_model` and follows the\ndocumented binding behavior:\n\n* ``await env.AI.run(model, {\"messages\": [...]})`` for chat models such\n  as ``@cf/meta/llama-3.1-8b-instruct`` (see\n  https://developers.cloudflare.com/workers-ai/configuration/bindings/\n  and https://developers.cloudflare.com/workers-ai/features/prompting/).\n* In Python Workers the call is ``await ai.run(model, {...})`` with a\n  plain Python dict -- no ``to_js`` glue needed since Python Workers GA\n  (see https://blog.cloudflare.com/python-workers-ga/, whose FastAPI\n  example calls ``await env.AI.run(...)`` directly).\n* Chat-completions style calls return an object shaped like\n  ``{\"response\": \"<generated text>\"}`` (see the model pages under\n  https://developers.cloudflare.com/workers-ai/models/, e.g.\n  llama-3.1-8b-instruct documents a ``response`` string field). Through\n  the Python FFI the response is attribute-style, i.e.\n  ``resp.response`` (see\n  ``src/cloudflare/internal/test/ai/ai-api-test.py`` in cloudflare/workerd).\n  :func:`run_model` therefore accepts both attribute-style and\n  dict-style responses.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport json\nfrom typing import Any\n\nfrom repository import get_incident\nfrom repository import list_findings as list_findings_from_db\nfrom repository import list_messages as list_messages_from_db\n\n#: Chat model used for the single investigation call. Kept as a module\n#: constant (and overridable per call) so the model choice stays\n#: configuration, not logic scattered through the service.\nDEFAULT_MODEL = \"@cf/meta/llama-3.1-8b-instruct\"\n\nSYSTEM_PROMPT = (\n    \"You are investigating a software/system incident. \"\n    \"Analyze the symptoms, identify likely causes, explain your reasoning \"\n    \"briefly, and suggest what should be checked next. \"\n    \"Do not claim anything was verified when it was not. \"\n    'Respond with JSON only, using exactly these keys: \"analysis\" (string), '\n    '\"possible_causes\" (array of strings), \"next_steps\" (array of strings).'\n)\n\n\nclass IncidentNotFoundError(ValueError):\n    \"\"\"Raised when no incident exists for the requested id.\"\"\"\n\n\ndef _format_messages(history: list[dict[str, Any]]) -> str:\n    if not history:\n        return \"(none)\"\n    return \"\\n\".join(\n        f\"- {m.get('role', '?')}: {m.get('content', '')}\" for m in history\n    )\n\n\ndef _format_findings(findings: list[dict[str, Any]]) -> str:\n    if not findings:\n        return \"(none)\"\n    return \"\\n\".join(\n        f\"- {f.get('title', '')}: {f.get('detail', '')}\" for f in findings\n    )\n\n\ndef build_investigation_messages(\n    incident: dict[str, Any],\n    history: list[dict[str, Any]],\n    findings: list[dict[str, Any]],\n) -> list[dict[str, str]]:\n    \"\"\"Build the ``messages`` payload sent to Workers AI.\n\n    Keeps the full incident record (title, symptoms, environment, status),\n    the previous messages (role + content only) and the existing findings\n    (title + detail only) so the model sees the whole investigation state.\n    \"\"\"\n    user_content = (\n        f\"Incident title: {incident.get('title', '')}\\n\"\n        f\"Symptoms: {incident.get('symptoms', '')}\\n\"\n        f\"Environment: {incident.get('environment', '')}\\n\"\n        f\"Status: {incident.get('status', '')}\\n\"\n        f\"\\nPrevious messages:\\n{_format_messages(history)}\\n\"\n        f\"\\nExisting findings:\\n{_format_findings(findings)}\"\n    )\n    return [\n        {\"role\": \"system\", \"content\": SYSTEM_PROMPT},\n        {\"role\": \"user\", \"content\": user_content},\n    ]\n\n\ndef _strip_code_fences(text: str) -> str:\n    text = text.strip()\n    if text.startswith(\"```\") and text.endswith(\"```\"):\n        text = text[3:-3].strip()\n        # Allow a leading language tag such as ```json\n        if \"\\n\" in text:\n            first_line, _, rest = text.partition(\"\\n\")\n            if first_line.strip() and not first_line.strip().startswith(\"{\"):\n                text = rest.strip()\n    return text\n\n\ndef parse_investigation_text(text: str) -> dict[str, Any]:\n    \"\"\"Parse the model's raw text into the structured investigation result.\n\n    Raises ``ValueError`` with the raw text attached when the model did\n    not return the expected JSON shape -- never silently returns a guess.\n    \"\"\"\n    cleaned = _strip_code_fences(text)\n    try:\n        data = json.loads(cleaned)\n    except json.JSONDecodeError as exc:\n        raise ValueError(\n            f\"Workers AI did not return valid JSON: {exc}; raw text: {text!r}\"\n        ) from exc\n    if not isinstance(data, dict):\n        raise ValueError(\n            f\"Workers AI must return a JSON object; raw text: {text!r}\"\n        )\n    analysis = data.get(\"analysis\")\n    possible_causes = data.get(\"possible_causes\")\n    next_steps = data.get(\"next_steps\")\n    if not isinstance(analysis, str) or not analysis.strip():\n        raise ValueError(\n            \"Workers AI result is missing a non-empty 'analysis' string; \"\n            f\"raw text: {text!r}\"\n        )\n    if not isinstance(possible_causes, list) or not all(\n        isinstance(c, str) for c in possible_causes\n    ):\n        raise ValueError(\n            \"Workers AI result 'possible_causes' must be an array of strings; \"\n            f\"raw text: {text!r}\"\n        )\n    if not isinstance(next_steps, list) or not all(\n        isinstance(s, str) for s in next_steps\n    ):\n        raise ValueError(\n            \"Workers AI result 'next_steps' must be an array of strings; \"\n            f\"raw text: {text!r}\"\n        )\n    return {\n        \"analysis\": analysis,\n        \"possible_causes\": possible_causes,\n        \"next_steps\": next_steps,\n    }\n\n\nasync def run_model(\n    ai: Any, model: str, messages: list[dict[str, str]]\n) -> str:\n    \"\"\"Make the single Workers AI call and return the generated text.\n\n    This is the only Workers AI-specific function. ``ai`` is the Workers\n    AI binding (``env.AI``); ``messages`` uses the documented scoped-prompt\n    shape ``[{\"role\": ..., \"content\": ...}]``. Any binding/model error\n    propagates unchanged.\n    \"\"\"\n    response = await ai.run(model, {\"messages\": messages})\n    text: Any = getattr(response, \"response\", None)\n    if text is None and isinstance(response, dict):\n        text = response.get(\"response\")\n    if text is None and hasattr(response, \"get\"):\n        try:\n            text = response.get(\"response\")  # type: ignore[union-attr]\n        except Exception:\n            text = None\n    if not isinstance(text, str) or not text.strip():\n        raise ValueError(\n            \"Workers AI returned an empty response \"\n            f\"for model {model!r}: {response!r}\"\n        )\n    return text\n\n\nasync def investigate_incident(\n    db: Any,\n    ai: Any,\n    incident_id: str,\n    model: str = DEFAULT_MODEL,\n) -> dict[str, Any]:\n    \"\"\"Run one investigation pass for an incident.\n\n    1. Load the incident via the repository; raise\n       :class:`IncidentNotFoundError` when absent.\n    2. Load previous messages and existing findings via the repository.\n    3. Build the Workers AI context.\n    4. Make one model call.\n    5. Return the structured result ``{\"analysis\", \"possible_causes\",\n       \"next_steps\"}``.\n\n    Nothing is written to ``messages`` or ``findings`` here.\n    \"\"\"\n    incident = await get_incident(db, incident_id)\n    if incident is None:\n        raise IncidentNotFoundError(f\"Incident not found: {incident_id}\")\n    history = await list_messages_from_db(db, incident_id)\n    findings = await list_findings_from_db(db, incident_id)\n    messages = build_investigation_messages(incident, history, findings)\n    raw_text = await run_model(ai, model, messages)\n    return parse_investigation_text(raw_text)\n",
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src/investigation.py"
}
```

**Output:**
```
Wrote file successfully.
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.7s)

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "Create src/investigation.py orchestration service",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Add tests/test_investigation.py with fakes",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Run test suite and verify",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "Create src/investigation.py orchestration service",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "Add tests/test_investigation.py with fakes",
    "status": "in_progress",
    "priority": "high"
  },
  {
    "content": "Run test suite and verify",
    "status": "pending",
    "priority": "high"
  }
]
```

---

## Assistant (Build · Muse Spark 1.3 Free · 13.3s)

_Thinking:_



**Tool: write**

**Input:**
```json
{
  "content": "\"\"\"Tests for the investigation orchestration service.\n\nFakes deliberately mirror the real runtime surfaces:\n\n- ``FakeD1Database`` behaves like the Cloudflare Python Workers D1\n  binding (``db.prepare(q).bind(*params)`` -> ``await .run()/.all()/\n  .first()``, attribute-style rows, errors propagate). The SQLite schema\n  is loaded from the real migration files.\n- ``FakeAI`` behaves like the Workers AI binding: ``await ai.run(model,\n  inputs)`` where ``inputs`` is a plain dict with a ``messages`` key,\n  returning an attribute-style object with a ``response`` string field\n  (matching ``ai-api-test.py`` in cloudflare/workerd). A dict-style\n  variant is also exercised since the FFI shape may surface either way.\n\"\"\"\n\nfrom __future__ import annotations\n\nimport json\nimport pathlib\nimport sqlite3\nimport sys\nimport types\nimport unittest\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSRC = ROOT / \"src\"\nMIGRATIONS = ROOT / \"migrations\"\nif str(SRC) not in sys.path:\n    sys.path.insert(0, str(SRC))\n\nimport investigation\nfrom investigation import IncidentNotFoundError, investigate_incident\n\n\nclass FakeD1Result:\n    def __init__(self, results: list[types.SimpleNamespace]) -> None:\n        self.results = results\n\n\nclass FakeD1BoundStatement:\n    def __init__(\n        self,\n        conn: sqlite3.Connection,\n        query: str,\n        params: tuple[object, ...],\n    ) -> None:\n        self._conn = conn\n        self._query = query\n        self._params = params\n\n    async def run(self) -> FakeD1Result:\n        self._conn.execute(self._query, self._params)\n        self._conn.commit()\n        return FakeD1Result([])\n\n    async def all(self) -> FakeD1Result:\n        cur = self._conn.execute(self._query, self._params)\n        cols = [d[0] for d in cur.description] if cur.description else []\n        rows = [types.SimpleNamespace(**dict(zip(cols, r))) for r in cur.fetchall()]\n        return FakeD1Result(rows)\n\n    async def first(self) -> types.SimpleNamespace | None:\n        result = await self.all()\n        return result.results[0] if result.results else None\n\n\nclass FakeD1PreparedStatement:\n    def __init__(self, conn: sqlite3.Connection, query: str) -> None:\n        self._conn = conn\n        self._query = query\n\n    def bind(self, *params: object) -> FakeD1BoundStatement:\n        return FakeD1BoundStatement(self._conn, self._query, params)\n\n\nclass FakeD1Database:\n    def __init__(self, conn: sqlite3.Connection) -> None:\n        self._conn = conn\n\n    def prepare(self, query: str) -> FakeD1PreparedStatement:\n        return FakeD1PreparedStatement(self._conn, query)\n\n\nclass FakeAI:\n    \"\"\"Attribute-style Workers AI response (``resp.response``).\"\"\"\n\n    def __init__(self, payload: dict[str, object]) -> None:\n        self.calls: list[tuple[str, dict[str, object]]] = []\n        self._payload = payload\n\n    async def run(\n        self, model: str, inputs: dict[str, object]\n    ) -> types.SimpleNamespace:\n        self.calls.append((model, inputs))\n        return types.SimpleNamespace(response=json.dumps(self._payload))\n\n\nclass FakeDictAI(FakeAI):\n    \"\"\"Dict-style Workers AI response (``resp['response']``).\"\"\"\n\n    async def run(self, model: str, inputs: dict[str, object]) -> dict[str, str]:\n        self.calls.append((model, inputs))\n        return {\"response\": json.dumps(self._payload)}\n\n\nclass FailingAI:\n    async def run(\n        self, model: str, inputs: dict[str, object]\n    ) -> types.SimpleNamespace:\n        raise RuntimeError(\"Workers AI is unavailable\")\n\n\ndef _load_schema(conn: sqlite3.Connection) -> None:\n    for name in (\n        \"0001_create_incidents.sql\",\n        \"0002_create_messages.sql\",\n        \"0003_create_findings.sql\",\n    ):\n        conn.executescript((MIGRATIONS / name).read_text())\n\n\nPAYLOAD = {\n    \"analysis\": \"502s point at the backend not accepting connections.\",\n    \"possible_causes\": [\"backend down\", \"wrong listen address\"],\n    \"next_steps\": [\"check systemd status\", \"curl localhost:8000\"],\n}\n\n\nclass InvestigationServiceTest(unittest.IsolatedAsyncioTestCase):\n    def setUp(self) -> None:\n        self.conn = sqlite3.connect(\":memory:\")\n        _load_schema(self.conn)\n        self.conn.execute(\n            \"INSERT INTO incidents \"\n            \"(id, title, symptoms, environment, status, created_at, updated_at) \"\n            \"VALUES (?, ?, ?, ?, ?, ?, ?)\",\n            (\n                \"inc-1\",\n                \"Nginx returns 502\",\n                \"Every API request returns 502 after restarting the backend.\",\n                \"Ubuntu server, Nginx, FastAPI as systemd service.\",\n                \"open\",\n                \"2026-09-27T10:00:00+00:00\",\n                \"2026-09-27T10:00:00+00:00\",\n            ),\n        )\n        self.conn.execute(\n            \"INSERT INTO messages \"\n            \"(id, incident_id, role, content, created_at, updated_at) \"\n            \"VALUES (?, ?, ?, ?, ?, ?)\",\n            (\n                \"msg-1\",\n                \"inc-1\",\n                \"user\",\n                \"The backend logs show connection refused.\",\n                \"2026-09-27T10:01:00+00:00\",\n                \"2026-09-27T10:01:00+00:00\",\n            ),\n        )\n        self.conn.execute(\n            \"INSERT INTO findings (id, incident_id, title, detail, created_at) \"\n            \"VALUES (?, ?, ?, ?, ?)\",\n            (\n                \"find-1\",\n                \"inc-1\",\n                \"Backend not listening\",\n                \"Nothing on port 8000.\",\n                \"2026-09-27T10:05:00+00:00\",\n            ),\n        )\n        self.conn.commit()\n        self.db = FakeD1Database(self.conn)\n\n    def tearDown(self) -> None:\n        self.conn.close()\n\n    async def test_happy_path_returns_structured_result(self) -> None:\n        ai = FakeAI(dict(PAYLOAD))\n        result = await investigate_incident(self.db, ai, \"inc-1\")\n        self.assertEqual(result, PAYLOAD)\n        self.assertEqual(\n            set(result.keys()), {\"analysis\", \"possible_causes\", \"next_steps\"}\n        )\n\n    async def test_default_model_is_used_unless_overridden(self) -> None:\n        ai = FakeAI(dict(PAYLOAD))\n        await investigate_incident(self.db, ai, \"inc-1\")\n        self.assertEqual(ai.calls[0][0], investigation.DEFAULT_MODEL)\n\n        ai2 = FakeAI(dict(PAYLOAD))\n        await investigate_incident(\n            self.db, ai2, \"inc-1\", model=\"@cf/meta/llama-3.3-70b-instruct-fp8-fast\"\n        )\n        self.assertEqual(\n            ai2.calls[0][0], \"@cf/meta/llama-3.3-70b-instruct-fp8-fast\"\n        )\n\n    async def test_context_includes_incident_history_and_findings(self) -> None:\n        ai = FakeAI(dict(PAYLOAD))\n        await investigate_incident(self.db, ai, \"inc-1\")\n        _, inputs = ai.calls[0]\n        messages = inputs[\"messages\"]\n        assert isinstance(messages, list)\n        roles = [m[\"role\"] for m in messages]\n        self.assertIn(\"system\", roles)\n        user_text = next(m[\"content\"] for m in messages if m[\"role\"] == \"user\")\n        for expected in (\n            \"Nginx returns 502\",  # title\n            \"Every API request returns 502\",  # symptoms\n            \"Ubuntu server\",  # environment\n            \"open\",  # status\n            \"connection refused\",  # previous message content\n            \"user\",  # previous message role\n            \"Backend not listening\",  # finding title\n            \"Nothing on port 8000.\",  # finding detail\n        ):\n            self.assertIn(expected, user_text)\n\n    async def test_missing_incident_raises_clear_error(self) -> None:\n        ai = FakeAI(dict(PAYLOAD))\n        with self.assertRaises(IncidentNotFoundError) as ctx:\n            await investigate_incident(self.db, ai, \"inc-missing\")\n        self.assertIn(\"inc-missing\", str(ctx.exception))\n        self.assertEqual(ai.calls, [])\n\n    async def test_dict_style_ai_response_is_accepted(self) -> None:\n        ai = FakeDictAI(dict(PAYLOAD))\n        result = await investigate_incident(self.db, ai, \"inc-1\")\n        self.assertEqual(result, PAYLOAD)\n\n    async def test_model_errors_surface(self) -> None:\n        with self.assertRaises(RuntimeError):\n            await investigate_incident(self.db, FailingAI(), \"inc-1\")\n\n    async def test_non_json_model_output_raises(self) -> None:\n        class PlainTextAI:\n            async def run(\n                self, model: str, inputs: dict[str, object]\n            ) -> types.SimpleNamespace:\n                return types.SimpleNamespace(response=\"just some prose\")\n\n        with self.assertRaises(ValueError):\n            await investigate_incident(self.db, PlainTextAI(), \"inc-1\")\n\n    async def test_nothing_is_persisted(self) -> None:\n        ai = FakeAI(dict(PAYLOAD))\n        await investigate_incident(self.db, ai, \"inc-1\")\n        self.assertEqual(\n            self.conn.execute(\"SELECT COUNT(*) FROM messages\").fetchone()[0], 1\n        )\n        self.assertEqual(\n            self.conn.execute(\"SELECT COUNT(*) FROM findings\").fetchone()[0], 1\n        )\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n",
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/tests/test_investigation.py"
}
```

**Output:**
```
Wrote file successfully.
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.3s)

**Tool: bash**

**Input:**
```json
{
  "command": "python3 -m unittest discover -s tests -v 2>&1 | tail -25",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
test_context_includes_incident_history_and_findings (test_investigation.InvestigationServiceTest.test_context_includes_incident_history_and_findings) ... ok
test_default_model_is_used_unless_overridden (test_investigation.InvestigationServiceTest.test_default_model_is_used_unless_overridden) ... ok
test_dict_style_ai_response_is_accepted (test_investigation.InvestigationServiceTest.test_dict_style_ai_response_is_accepted) ... ok
test_happy_path_returns_structured_result (test_investigation.InvestigationServiceTest.test_happy_path_returns_structured_result) ... ok
test_missing_incident_raises_clear_error (test_investigation.InvestigationServiceTest.test_missing_incident_raises_clear_error) ... ok
test_model_errors_surface (test_investigation.InvestigationServiceTest.test_model_errors_surface) ... ok
test_non_json_model_output_raises (test_investigation.InvestigationServiceTest.test_non_json_model_output_raises) ... ok
test_nothing_is_persisted (test_investigation.InvestigationServiceTest.test_nothing_is_persisted) ... ok
test_create_finding_inserts_all_fields (test_repository.RepositoryMessagesFindingsTest.test_create_finding_inserts_all_fields) ... ok
test_create_message_inserts_all_fields (test_repository.RepositoryMessagesFindingsTest.test_create_message_inserts_all_fields) ... ok
test_errors_are_not_swallowed (test_repository.RepositoryMessagesFindingsTest.test_errors_are_not_swallowed) ... ok
test_list_findings_orders_and_isolates_incident (test_repository.RepositoryMessagesFindingsTest.test_list_findings_orders_and_isolates_incident) ... ok
test_list_messages_orders_for_conversation_history (test_repository.RepositoryMessagesFindingsTest.test_list_messages_orders_for_conversation_history) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.041s

OK

```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.4s)

_Thinking:_



_Thinking:_



**Tool: bash**

**Input:**
```json
{
  "command": "python3 -m pyrefly check src/investigation.py 2>&1 | tail -10 || .venv/bin/pyrefly check src/investigation.py 2>&1 | tail -10",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
/home/akhileshmt/Documents/Fun/wtf-error/.venv-workers/bin/python3: No module named pyrefly

```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.8s)

**Tool: bash**

**Input:**
```json
{
  "command": "ls .venv/bin/ | grep -i -E \"pyrefly|ruff|mypy\"; .venv/bin/python -c \"import investigation\" 2>&1 | tail -3",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error/src"
}
```

**Output:**
```
ls: cannot access '.venv/bin/': No such file or directory
zsh:1: no such file or directory: .venv/bin/python

```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.5s)

**Tool: bash**

**Input:**
```json
{
  "command": "python3 -c \"import ast; ast.parse(open('src/investigation.py').read()); ast.parse(open('tests/test_investigation.py').read()); print('syntax OK')\"",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
syntax OK

```

---

## Assistant (Build · Muse Spark 1.3 Free · 1.8s)

**Tool: todowrite**

**Input:**
```json
{
  "todos": [
    {
      "content": "Create src/investigation.py orchestration service",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Add tests/test_investigation.py with fakes",
      "status": "completed",
      "priority": "high"
    },
    {
      "content": "Run test suite and verify",
      "status": "completed",
      "priority": "high"
    }
  ]
}
```

**Output:**
```
[
  {
    "content": "Create src/investigation.py orchestration service",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "Add tests/test_investigation.py with fakes",
    "status": "completed",
    "priority": "high"
  },
  {
    "content": "Run test suite and verify",
    "status": "completed",
    "priority": "high"
  }
]
```

---

## Assistant (Build · Muse Spark 1.3 Free · 15.4s)

_Thinking:_



Done. The first version of the investigation service is in place, orchestration only.

## 1. What file/function was added

**`src/investigation.py`** — no routes, no SQL, no persistence. Main entry point:

```python
async def investigate_incident(db, ai, incident_id, model=DEFAULT_MODEL)
```

Helpers around it:
- `build_investigation_messages(incident, history, findings)` — pure context builder.
- `run_model(ai, model, messages)` — the only Workers AI-specific code (one `await ai.run(...)` call + response extraction).
- `parse_investigation_text(text)` — parses the model's raw text into the structured result; raises `ValueError` (with raw text attached) on bad shape instead of guessing.
- `IncidentNotFoundError(ValueError)` — raised as `Incident not found: <id>` when the incident is absent.
- `SYSTEM_PROMPT` + `DEFAULT_MODEL` constants.

Flow is exactly: `get_incident` → `list_messages` → `list_findings` (all existing repository functions) → build messages → one `ai.run` → parse → return. Nothing is written to `messages`/`findings`.

## 2. How context is built

`build_investigation_messages` returns a two-message scoped prompt:
- `system`: role instructions (analyze symptoms, likely causes, brief reasoning, next checks, never claim unverified things, JSON-only with exactly `analysis` / `possible_causes` / `next_steps`).
- `user`: the incident's `title`, `symptoms`, `environment`, `status`, then previous messages as `- <role>: <content>` lines (`(none)` when empty), then existing findings as `- <title>: <detail>` lines.

One spec note: you asked for findings as title/evidence/confidence, but the real `findings` table (`migrations/0003_create_findings.sql`) and `list_findings` return `title`/`detail`. The service uses the actual schema (`title` + `detail`).

## 3. Which model is called

`DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct"`, overridable per call via the `model=` parameter. Chosen because it's a chat model with the simple, stable `{messages: [...]}` input shape and is on the documented JSON-mode-compatible list, so a structured-JSON prompt is idiomatic for it. I deliberately did **not** use `response_format: json_schema` enforcement yet — the prompt asks for JSON-only and the parser validates strictly, which keeps this version to one clean call without schema-negotiation failure modes.

## 4. Exact response shape

```python
{"analysis": str, "possible_causes": list[str], "next_steps": list[str]}
```

Exactly these three keys — validated types/non-empty `analysis`, extra keys dropped. `incident_id`/`model` are intentionally not included so the contract matches the spec and the next step can decide what to persist.

## 5. Cloudflare docs/binding behavior relied on

- **Call shape** `await env.AI.run(model, {"messages": [...]})` for chat models: `workers-ai/configuration/bindings` and `workers-ai/features/prompting` (scoped `role`/`content` prompts).
- **Python Workers calling convention** — plain-dict args, no `to_js` glue: Python Workers GA blog (`blog.cloudflare.com/python-workers-ga`), whose FastAPI example calls `await env.AI.run(...)` directly off `request.scope["env"]`. Our `ai` param is that same `env.AI` binding.
- **Response shape** `{"response": "<text>"}` for this model family: the Workers AI model pages (llama-3.1-8b-instruct documents a `response` string output).
- **Attribute-style access in Python** (`resp.response`): `cloudflare/workerd` `src/cloudflare/internal/test/ai/ai-api-test.py`. `run_model` therefore reads `response.response` first, falls back to dict-style `response["response"]`/`response.get(...)`, and raises `ValueError` on empty text. Binding/model exceptions propagate untouched.
- I did **not** add the `"ai": {"binding": "AI"}` block to `wrangler.jsonc` — not needed for this orchestration step, but deployment will need it before any live call.

## 6. Tests run

- New `tests/test_investigation.py` (8 tests): happy-path shape, default vs. overridden model, context contains all 8 expected incident/history/finding fragments, missing incident raises with the id and makes zero AI calls, dict-style AI response accepted, `RuntimeError` from AI surfaces, non-JSON model text raises `ValueError`, row counts unchanged (nothing persisted). Fakes mirror the real surfaces: SQLite backed by the actual migration files + attribute-style D1 rows, and an AI fake recording `(model, inputs)`.
- Full suite: `python3 -m unittest discover -s tests -v` → **13 tests, all OK** (5 pre-existing repository tests still pass).
- `ast.parse` syntax check on both new files → OK. (`pyrefly` isn't installed in this env, so no type-check run.)

## 7. Real Workers AI vs. mocks

**Mocks/local only — not tested against live Workers AI.** No `wrangler dev`/`deploy` call, no account credentials used, no network call made. The binding contract above is taken from docs + workerd's own Python AI test, and the fakes replicate exactly that surface, but the first live call (which also needs the `ai` binding added to `wrangler.jsonc`) is still unverified.

---

