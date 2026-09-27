# Cleanup repository.py for incidents table

**Session ID:** ses_f1bfef7dbffeJFSNLNDT39shaW
**Created:** 9/27/2026, 11:24:28 PM
**Updated:** 9/27/2026, 11:29:08 PM

---

## User

The D1 migration is done.

Now clean up `src/repository.py` so it matches the `incidents` table exactly.

The table has these fields:

- `id`
- `title`
- `symptoms`
- `environment`
- `status`
- `created_at`
- `updated_at`

Only keep these 3 functions:

`create_incident(db, incident)`

- `incident` is already a complete dictionary.
- Insert all 7 fields.
- Do not generate the ID, status, or timestamps here.
- The caller already provides them.
- After the insert works, return the inserted incident record.

`get_incident(db, incident_id)`

- Find the incident by ID.
- Return it as a normal Python dictionary.
- If it does not exist, return `None`.

`list_incidents(db, limit=20, offset=0)`

- Return incidents as a normal Python list of dictionaries.
- Order by:
  `created_at DESC, id DESC`
- Support `limit` and `offset`.

Remove the `last_row_id` logic.

Also remove the fallback that gets the latest incident after an insert. That is unsafe because another request could insert an incident at the same time and we could return the wrong one.

The repository currently tries to support too many different result formats and test mocks. Remove that complexity.

Only support the real Cloudflare Python Workers D1 binding.

If needed, check the Cloudflare docs to confirm how D1 query results should be converted into normal Python dictionaries/lists.

Use parameterized SQL queries.

Do not hide errors.

If D1 fails, conversion fails, or something 

---

## Assistant (Build · Muse Spark 1.3 Free · 3.6s)

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
uv.lock
wrangler.jsonc

(20 entries)
</entries>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 1.9s)

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
3: Uses the D1 Python Workers async binding API::
4: 
5:     db.prepare("SELECT ... WHERE id = ?").bind(incident_id).first()
6:     db.prepare("INSERT INTO ...").bind(...).run()
7:     db.prepare("SELECT ...").bind(...).all()  # ``run()`` is an alias
8: 
9: ``db`` is the D1 database binding (e.g. ``env.DB`` or, inside FastAPI,
10: ``request.scope["env"].DB``). All functions are async and return plain
11: Python dicts so results are JSON-serializable.
12: """
13: 
14: from __future__ import annotations
15: 
16: from typing import Any, Mapping, TypeVar
17: 
18: _T = TypeVar("_T")
19: 
20: try:  # pragma: no cover - typing only, runtime uses duck-typing
21:     from schemas import IncidentCreate
22: except Exception:  # pragma: no cover - repo-root layout or broken schema
23:     try:
24:         from src.schemas import IncidentCreate  # type: ignore[no-redef]
25:     except Exception:
26:         IncidentCreate = Any  # type: ignore[no-redef,misc]
27: 
28: TABLE = "incidents"
29: COLUMNS = "id, title, symptoms, environment, created_at"
30: _RECORD_KEYS = ("id", "title", "symptoms", "environment", "created_at")
31: 
32: 
33: class RepositoryHelpers:
34:     """Internal D1 helpers grouped as static methods."""
35: 
36:     @staticmethod
37:     def _incident_fields(incident: Any) -> tuple[Any, Any, Any]:
38:         """Extract (title, symptoms, environment) from a model or mapping."""
39:         if isinstance(incident, Mapping):
40:             return incident["title"], incident["symptoms"], incident["environment"]
41:         if isinstance(incident, dict):  # pragma: no cover - Mapping covers this
42:             return incident["title"], incident["symptoms"], incident["environment"]
43:         # Pydantic model (IncidentCreate) or any object with attributes.
44:         if hasattr(incident, "model_dump"):
45:             try:
46:                 data = incident.model_dump()
47:                 if isinstance(data, dict):
48:                     return data["title"], data["symptoms"], data["environment"]
49:             except Exception:
50:                 pass
51:         if isinstance(incident, (list, tuple)) and len(incident) == 3:
52:             return incident[0], incident[1], incident[2]
53:         return incident.title, incident.symptoms, incident.environment
54: 
55:     @staticmethod
56:     def _maybe_to_py(value: _T) -> _T:
57:         """Convert a Pyodide JsProxy to plain Python when possible."""
58:         if value is None:
59:             return value
60:         to_py = getattr(value, "to_py", None)
61:         if callable(to_py):
62:             try:
63:                 converted: _T = to_py()
64:                 return converted
65:             except Exception:
66:                 return value
67:         return value
68: 
69:     @staticmethod
70:     def _row_to_dict(row: Any) -> dict[str, Any] | None:
71:         """Normalize a single D1 row (JS object, dict, or attribute object)."""
72:         if row is None:
73:             return None
74:         row = RepositoryHelpers._maybe_to_py(row)
75:         if row is None:
76:             return None
77:         if isinstance(row, dict):
78:             return dict(row)
79:         if isinstance(row, Mapping):
80:             return dict(row)
81: 
82:         # Attribute-style row (real D1 binding exposes columns as attributes,
83:         # e.g. ``row.id`` as in the fastapi-todo example).
84:         try:
85:             record: dict[str, Any] = {}
86:             found = False
87:             for key in _RECORD_KEYS:
88:                 if hasattr(row, key):
89:                     record[key] = RepositoryHelpers._maybe_to_py(getattr(row, key))
90:                     found = True
91:                 elif isinstance(row, (list, tuple)):
92:                     break
93:                 else:
94:                     try:
95:                         record[key] = RepositoryHelpers._maybe_to_py(row[key])  # type: ignore[index]
96:                         found = True
97:                     except Exception:
98:                         continue
99:             if found:
100:                 return record
101:         except Exception:
102:             pass
103: 
104:         # Fallbacks for mock objects.
105:         for attr in ("__dict__",):
106:             try:
107:                 data = getattr(row, attr)
108:                 if isinstance(data, dict) and data:
109:                     return {k: RepositoryHelpers._maybe_to_py(v) for k, v in data.items()}
110:             except Exception:
111:                 continue
112:         try:
113:             return dict(row)
114:         except Exception:
115:             pass
116:         try:
117:             return dict(vars(row))
118:         except Exception:
119:             pass
120:         return None
121: 
122:     @staticmethod
123:     def _result_rows(result: Any) -> list[Any]:
124:         """Extract the row list from a D1Result (``run()``/``all()`` output)."""
125:         if result is None:
126:             return []
127:         results: Any = getattr(result, "results", None) if not isinstance(result, dict) else result.get("results")
128:         if results is None and isinstance(result, Mapping):
129:             results = result.get("results")
130:         if results is None and isinstance(result, (list, tuple)):
131:             return list(result)
132:         if results is None:
133:             converted = RepositoryHelpers._maybe_to_py(result)
134:             if isinstance(converted, dict) and "results" in converted:
135:                 results = converted["results"]
136:             elif isinstance(converted, (list, tuple)):
137:                 return list(converted)
138:             else:
139:                 return []
140:         results = RepositoryHelpers._maybe_to_py(results)
141:         if results is None:
142:             return []
143:         if isinstance(results, (list, tuple)):
144:             return list(results)
145:         try:
146:             return list(results)
147:         except Exception:
148:             return []
149: 
150:     @staticmethod
151:     def _is_success(result: Any) -> bool:
152:         """Return False only when D1 explicitly reports failure."""
153:         try:
154:             if isinstance(result, dict):
155:                 success = result.get("success", True)
156:             else:
157:                 success = getattr(result, "success", True)
158:                 if isinstance(success, dict):
159:                     success = True
160:             success = RepositoryHelpers._maybe_to_py(success)
161:             if isinstance(success, bool):
162:                 return success
163:             if success is None:
164:                 return True
165:             return bool(success)
166:         except Exception:
167:             return True
168: 
169:     @staticmethod
170:     def _coerce_row_id(value: object) -> int | str | None:
171:         """Narrow an arbitrary meta value to a usable row id."""
172:         if value is None:
173:             return None
174:         if isinstance(value, bool):
175:             return None
176:         if isinstance(value, int):
177:             return value
178:         if isinstance(value, str):
179:             return value if value != "" else None
180:         if isinstance(value, float) and value.is_integer():
181:             return int(value)
182:         return None
183: 
184:     @staticmethod
185:     def _last_row_id(result: Any) -> int | str | None:
186:         """Extract ``meta.last_row_id`` from dict- or attribute-style results."""
187:         candidates: list[Any] = []
188:         try:
189:             if isinstance(result, dict):
190:                 meta = result.get("meta")
191:                 candidates.append(meta.get("last_row_id") if isinstance(meta, dict) else None)
192:                 candidates.append(result.get("last_row_id"))
193:             else:
194:                 meta = getattr(result, "meta", None)
195:                 if meta is not None:
196:                     if isinstance(meta, dict):
197:                         candidates.append(meta.get("last_row_id"))
198:                     else:
199:                         candidates.append(getattr(meta, "last_row_id", None))
200:                         try:
201:                             candidates.append(meta["last_row_id"])  # type: ignore[index]
202:                         except Exception:
203:                             pass
204:                 candidates.append(getattr(result, "last_row_id", None))
205:         except Exception:
206:             pass
207:         # Also try a to_py-converted payload.
208:         try:
209:             converted = RepositoryHelpers._maybe_to_py(result)
210:             if isinstance(converted, dict):
211:                 meta_obj = converted.get("meta")
212:                 if isinstance(meta_obj, dict):
213:                     coerced = RepositoryHelpers._coerce_row_id(meta_obj.get("last_row_id"))
214:                     if coerced is not None and coerced != 0:
215:                         return coerced
216:         except Exception:
217:             pass
218:         for value in candidates:
219:             coerced = RepositoryHelpers._coerce_row_id(RepositoryHelpers._maybe_to_py(value))
220:             if coerced is not None and coerced != 0:
221:                 return coerced
222:         # ``0`` is D1's sentinel for non-inserts; report None when nothing real.
223:         return None
224: 
225:     @staticmethod
226:     async def _execute_run(bound_stmt: Any) -> Any:
227:         """Await ``run()`` (falling back to ``all()`` for minimal mocks)."""
228:         run = getattr(bound_stmt, "run", None)
229:         if callable(run):
230:             return await run()
231:         all_fn = getattr(bound_stmt, "all", None)
232:         if callable(all_fn):
233:             return await all_fn()
234:         raise AttributeError("D1 statement has neither run() nor all()")
235: 
236:     @staticmethod
237:     async def _fetch_all(bound_stmt: Any) -> Any:
238:         """Await ``all()`` (falling back to ``run()``, which D1 aliases)."""
239:         all_fn = getattr(bound_stmt, "all", None)
240:         if callable(all_fn):
241:             return await all_fn()
242:         run = getattr(bound_stmt, "run", None)
243:         if callable(run):
244:             return await run()
245:         raise AttributeError("D1 statement has neither all() nor run()")
246: 
247: 
248: async def create_incident(db: Any, incident: Any) -> dict[str, Any] | None:
249:     """Insert a complete incident record, then return it.
250: 
251:     The insert is awaited first; the freshly inserted row is read back
252:     (via ``meta.last_row_id``) only after the insert succeeds.
253:     """
254:     title, symptoms, environment = RepositoryHelpers._incident_fields(incident)
255: 
256:     insert_stmt = db.prepare(
257:         f"INSERT INTO {TABLE} (title, symptoms, environment) VALUES (?, ?, ?)"
258:     ).bind(title, symptoms, environment)
259:     insert_result = await RepositoryHelpers._execute_run(insert_stmt)
260: 
261:     if not RepositoryHelpers._is_success(insert_result):
262:         raise RuntimeError("Failed to insert incident")
263: 
264:     last_id = RepositoryHelpers._last_row_id(insert_result)
265:     if last_id is not None:
266:         row = (
267:             await db.prepare(
268:                 f"SELECT {COLUMNS} FROM {TABLE} WHERE id = ? LIMIT 1"
269:             )
270:             .bind(last_id)
271:             .first()
272:         )
273:         record = RepositoryHelpers._row_to_dict(row)
274:         if record is not None:
275:             return record
276: 
277:     # Fallback when the binding does not surface last_row_id (e.g. some
278:     # mocks): return the most recently created row.
279:     row = (
280:         await db.prepare(
281:             f"SELECT {COLUMNS} FROM {TABLE} ORDER BY id DESC LIMIT 1"
282:         ).first()
283:     )
284:     return RepositoryHelpers._row_to_dict(row)
285: 
286: 
287: async def get_incident(db: Any, incident_id: Any) -> dict[str, Any] | None:
288:     """Return a single incident record, or None if absent."""
289:     row = (
290:         await db.prepare(f"SELECT {COLUMNS} FROM {TABLE} WHERE id = ? LIMIT 1")
291:         .bind(incident_id)
292:         .first()
293:     )
294:     return RepositoryHelpers._row_to_dict(row)
295: 
296: 
297: async def list_incidents(db: Any, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
298:     """Return incidents ordered by created_at DESC, id DESC."""
299:     bound = db.prepare(
300:         f"SELECT {COLUMNS} FROM {TABLE} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
301:     ).bind(limit, offset)
302:     result = await RepositoryHelpers._fetch_all(bound)
303:     records: list[dict[str, Any]] = []
304:     for row in RepositoryHelpers._result_rows(result):
305:         record = RepositoryHelpers._row_to_dict(row)
306:         if record is not None:
307:             records.append(record)
308:     return records

(End of file - total 308 lines)
</content>
```

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

---

## Assistant (Build · Muse Spark 1.3 Free · 2.5s)

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

(1 entries)
</entries>
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
1: from fastapi import FastAPI
2: from workers import asgi
3: 
4: app = FastAPI(title="wtf-error")
5: 
6: 
7: @app.get("/health")
8: async def health() -> dict[str, str]:
9:     return {"status": "ok", "service": "wtf-error"}
10: 
11: 
12: Default = asgi.entrypoint(app)

(End of file - total 12 lines)
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

(End of file - total 19 lines)
</content>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 1.7s)

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

---

## Assistant (Build · Muse Spark 1.3 Free · 6.3s)

_Thinking:_

Refactoring repository functions to match the incident schema and D1 constraints, removing legacy logic and mocks.

_Thinking:_



**Tool: websearch**

**Input:**
```json
{
  "query": "Cloudflare Python Workers D1 binding prepare bind first all run 2026",
  "type": "deep"
}
```

**Output:**
```
{
  "search_id": "search_c74bdcd350bb73c6bdae0af9c4a65f14",
  "results": [
    {
      "url": "https://developers.cloudflare.com/d1/worker-api/index.md",
      "title": "Workers Binding API",
      "publish_date": null,
      "excerpts": [
        "description: Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results. title: Workers Binding API image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt Use this file to discover all available pages before exploring further.\nWorkers Binding API\nLast updated Apr 21, 2026|Copy as Markdown|View as Markdown|Agent setup\nYou can execute SQL queries on your D1 database from a Worker using the Worker Binding API. To do this, you can perform the following steps:\n1. Bind the D1 Database.\n2. Prepare a statement.\n3. Run the prepared statement.\n4. Analyze the return object (if necessary).\n  Refer to the relevant sections for the API documentation.\nTypeScript support\nD1 Worker Bindings API is fully-typed via the runtime types generated by running wrangler types package, and also supports generic types ↗ as part of its TypeScript API. A generic type allows you to provide an optional type parameter so that a function understands the type of the data it is handling.\nWhen using the query statement methods D1PreparedStatement::run, D1PreparedStatement::raw and D1PreparedStatement::first, you can provide a type representing each database row. D1's API will return the result object with the correct type.\n// Elsewhere in your application\n// env.MY_DB is the D1 database binding from your Wrangler configuration file\nconst result = await env.MY_DB.prepare(\n\"SELECT Id, CustomerName, OrderDate FROM [Order] ORDER BY ShippedDate DESC LIMIT 100\",\n).run<OrderRow>();\nType conversion\nReplace the contents of your index.js file with the code below to view the effect of each API.\nindex.js\n// D1 API Playground - Test each D1 Worker Binding API method\n// Change the URL pathname to test different methods (e.g., /RUN, /RAW, /FIRST)\nexport default {\nasync fetch(request, env) {\nconst { pathname } = new URL(request.url);\n```\n\tconst session = env.DB.withSession(\"first-primary\")\n\tconst sessionStmt = session.prepare(`SELECT * FROM Customers WHERE CompanyName = ?`);\n\n  // Test D1PreparedStatement::run - returns full D1Result object\n  if (pathname === `/RUN`){\n\tconst returnValue = await stmt.bind(companyName1).run();\n\treturn Response.json(returnValue);\n\n```\n```\n  // Test D1PreparedStatement::raw - returns array of arrays\n} else if (pathname === `/RAW`){\n\tconst returnValue = await stmt.bind(companyName1).raw();\n\treturn Response.json(returnValue);\n\n  // Test D1PreparedStatement::first - returns first row only\n} else if (pathname === `/FIRST`){\n```\n```\n\tconst returnValue = await stmt.bind(companyName1).first();\n\treturn Response.json(returnValue);\n\n  // Test D1Database::batch - execute multiple statements\n} else if (pathname === `/BATCH`) {\n\tconst batchResult = await env.DB.batch([\n\t\tstmt.bind(companyName1),\n\t\tstmt.bind(companyName2)\n\t]);\n\treturn Response.json(batchResult);\n\n```"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api/",
      "title": "Workers Binding API · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "Docs {\"@context\":\"https://schema.org\",\"@type\":\"WebPage\",\"@id\":\"https://developers.cloudflare.com/d1/worker-api/#page\",\"headline\":\"Workers Binding API\",\"description\":\"Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results.\",\"url\":\"https://developers.cloudflare.com/d1/worker-api/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-04-21\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"description\":\"One platform for your apps, agents, and workforce. description: Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results. title: Workers Binding API image: https://developers.cloudflare.com/og-docs.png\nSkip"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/cloudflare-for-platforms/workers-for-platforms/configuration/bindings/index.md",
      "title": "Bindings",
      "publish_date": null,
      "excerpts": [
        "description: Attach KV, R2, D1, and other resource bindings to user Workers deployed through Workers for Platforms. title: Bindings image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/cloudflare-for-platforms/llms.txt Use this file to discover all available pages before exploring further.\nBindings\nLast updated Jul 22, 2026|Copy as Markdown|View as Markdown|Agent setup\nWhen you deploy User Workers through Workers for Platforms, you can attach bindings to give them access to resources like KV namespaces, D1 databases, R2 buckets, and more.\nThis enables your end customers to build more powerful applications without you having to build the infrastructure components yourself.\nWith bindings, each User Worker can extend functionality to:\n* Store data with KV, R2, D1, or Durable Objects\n* Process work asynchronously with Queues and Workflows\n* Run containers with Containers (bound as a Durable Object)\n* Connect to private networks with VPC Services, VPC Networks, and Hyperdrive\n* Collect metrics with Analytics Engine\nResource isolation\nEach User Worker can only access the bindings that are explicitly attached to it. For complete isolation, you can create and attach a unique resource (like a D1 database or KV namespace) to every User Worker.\n<Resource Isolation Model>\nResource Isolation Model\nAdding a KV Namespace to a User Worker\nThis example walks through how to create a KV namespace and attach it to a User Worker. The same process can be used to attach to other bindings.\n1. Create a KV namespace\nCreate a KV namespace using the Cloudflare API.\n2. Attach the KV namespace to the User Worker\nUse the Upload User Worker API to attach the KV namespace binding to the Worker. You can do this when you're first uploading the Worker script or when updating an existing Worker.\nNote\nWhen using the API to upload scripts, bindings must be specified in the metadata object of your multipart upload request.\n\"namespace_id\": \"<your-namespace-id>\"\n}\n]\n}'\n-F 'worker.js=@/path/to/worker.js'\nNow, the User Worker can access the USER_KV binding through the env argument using env.USER_KV.get(), env.USER_KV.put(), and other KV methods.\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/cloudflare-for-platforms/workers-for-platforms/configuration/bindings/#page\",\"headline\":\"Bindings · Cloudflare for Platforms docs\",\"description\":\"Attach KV, R2, D1, and other resource bindings to user Workers deployed through Workers for\nPlatforms.\",\"url\":\"https://developers.cloudflare.com/cloudflare-for-platforms/workers-for-platforms/configuration/bindings/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-07-22\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"description\":\"One platform for your apps, agents, and workforce."
      ]
    },
    {
      "url": "https://2c1dc640.preview.developers.cloudflare.com/d1/worker-api/",
      "title": "Workers Binding API · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "description: \"You can execute SQL queries on your D1 database from a Worker using the Worker Binding API. To do this, you can perform the following steps:\" title: Workers Binding API · Cloudflare D1 docs image: https://developers.cloudflare.com/dev-products-preview.png\nSkip to content\nWas this helpful?\nEdit Issue\nWorkers Binding API\nCopy Page You can execute SQL queries on your D1 database from a Worker using the Worker Binding API. To do this, you can perform the following steps:\nBind the D1 Database.\nPrepare a statement.\nRun the prepared statement.\nAnalyze the return object (if necessary). Refer to the relevant sections for the API documentation.\nTypeScript support D1 Worker Bindings API is fully-typed via the @cloudflare/workers-types package, and also supports generic types ↗ as"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python",
      "title": "Write Cloudflare Workers in Python",
      "publish_date": null,
      "excerpts": [
        "Write Cloudflare Workers in Python\nJun 22, 2026 — Workers Platform accessible via bindings , including: State storage and databases like KV, D1, Durable Objects. R2 Durable Workflows, Queues,"
      ]
    },
    {
      "url": "https://55041f86.previews.developers.cloudflare.com/d1/worker-api/d1-database/",
      "title": "D1 Database · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "Methods\nprepare()\nPrepares a query statement to be later executed. JavaScript Python const someVariable = Bs Beverages ; const stmt = env. DB . prepare ( \"SELECT * FROM Customers WHERE CompanyName = ?\" ). bind (someVariable); some_variable = \"Bs Beverages\" stmt = self .env. DB .prepare( \"SELECT * FROM Customers WHERE CompanyName = ?\" ).bind(some_variable)\nParameters\nquery : String Required\nThe SQL query you wish to execute on the database.\nReturn values\nD1PreparedStatement : Object\nAn object which only contains methods. Refer to Prepared statement methods .\nGuidance\nYou can use the bind method to dynamically bind a value into the query statement, as shown below. This method is equivalent to D1Database::prepare .\nbatch()\nThis method is equivalent to D1Database::batch . Previous Overview"
      ]
    },
    {
      "url": "https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/d1/worker-api/prepared-statements.mdx",
      "title": "cloudflare-docs/src/content/docs/d1/worker-api/prepared-statements.mdx at production · cloudflare/cloudflare-docs · GitHub",
      "publish_date": null,
      "excerpts": [
        "cloudflare/cloudflare-docs — src/content/docs/d1/worker-api/prepared-statements.mdx\n* Page: GitHub code file\n* URL: https://github.com/cloudflare/cloudflare-docs/blob/production/src/content/docs/d1/worker-api/prepared-statements.mdx\n* Repository: cloudflare/cloudflare-docs\n* Path: src/content/docs/d1/worker-api/prepared-statements.mdx\n* Ref: production\n* Lines: 435\ntitle: Prepared statement methods\ndescription: Bind parameters and run D1 prepared statements using the run, all, first, and raw methods.\npcx_content_type: concept\nsidebar:\norder: 2\nproducts:\n- d1\nimport { Type, MetaInfo, Details, Tabs, TabItem } from \"~/components\";\nThis chapter documents the various ways you can run and retrieve the results of a query after you have [prepared your statement](/d1/worker-api/d1-database/#prepare).\nMethods > `bind()`\n```js\n* D1 follows the SQLite convention for prepared statements parameter binding. Currently, D1 only supports Ordered (?NNNN) and Anonymous (?) parameters. In the future, D1 will support named parameters as well.\n* Syntax | Type | Description\n```"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/runtime-apis/bindings",
      "title": "Bindings (env) - Workers",
      "publish_date": null,
      "excerpts": [
        "Bindings (env) - Workers\nJul 22, 2026 — Bindings allow your Worker to interact with resources on the Cloudflare Developer Platform. Bindings provide better performance and less"
      ]
    },
    {
      "url": "http://developers.cloudflare.com/workers",
      "title": "Cloudflare Workers",
      "publish_date": null,
      "excerpts": [
        "Cloudflare Workers A serverless platform for building, deploying, and scaling apps across [Cloudflare's global network ↗](https://www.cloudflare.com/network/) with a single command — no infrastructure to manage, no complex configuration With Cloudflare Workers, you can expect to: ... Get started for free and grow with flexible [pricing](https://developers.cloudflare.com/workers/platform/pricing/), affordable at any scale Get started with your first project: [Deploy a template](https://dash.cloudflare.com/?to=/:account/workers-and-pages/templates) [Deploy with Wrangler CLI](https://developers.cloudflare.com/workers/get-started/guide/) Build with Workers Front-end applications Deploy [static assets](https://developers.cloudflare.com/workers/static-assets/) to Cloudflare's [CDN & cache](https://developers.cloudflare.com/cache/) for fast rendering Back-end applications Build APIs and connect to data stores with [Smart Placement](https://developers.cloudflare.com/workers/configuration/placement/) to optimize latency Serverless AI inference Run LLMs, generate images, and more with [Workers AI](https://developers.cloudflare.com/workers-ai/) ... Observability & monitoring Monitor performance, debug issues, and analyze traffic with [real-time logs](https://developers.cloudflare.com/workers/observability/logs/) and [analytics](https://developers.cloudflare.com/workers/observability/metrics-and-analytics/) Integrate with Workers Connect to external services like databases, APIs, and storage via [Bindings](https://developers.cloudflare.com/workers/runtime-apis/bindings/), enabling functionality with just a few lines of code: **Storage** [Durable Objects](https://developers.cloudflare.com/durable-objects/) Scalable stateful storage for real-time coordination. [D1](https://developers.cloudflare.com/d1/) Serverless SQL database built for fast, global queries. [KV](https://developers.cloudflare.com/kv/) Low-latency key-value storage for fast, edge-cached reads. [Queues](https://developers.cloudflare.com/queues/) Guaranteed delivery with no charges for egress bandwidth. [Hyperdrive](https://developers.cloudflare.com/hyperdrive/) Connect to your external database with accelerated queries, cached at the edge. **Compute** [Workers AI](https://developers.cloudflare.com/workers-ai/) Machine learning models powered by serverless GPUs. [Workflows](https://developers.cloudflare.com/workflows/) Durable, long-running operations with automatic retries. [Vectorize](https://developers.cloudflare.com/vectorize/) Vector database for AI-powered semantic search. [R2](https://developers.cloudflare.com/r2/) Zero-egress object storage for cost-efficient data access. [Browser Run](https://developers.cloudflare.com/browser-run/) Programmatic serverless browser instances. **Media** [Cache / CDN](https://developers.cloudflare.com/cache/) Global caching for high-performance, low-latency delivery."
      ]
    },
    {
      "url": "https://registry.terraform.io/providers/cloudflare/cloudflare/4.38.0/docs/resources/worker_script",
      "title": "cloudflare_worker_script | Resources | cloudflare/cloudflare | Terraform | Terraform Registry",
      "publish_date": null,
      "excerpts": [
        "database_id (String) Database ID of D1 database to use.\nname (String) The global variable for the binding in your Worker code.\nNested Schema for kv_namespace_binding\nRequired:\nname (String) The global variable for the binding in your Worker code.\nnamespace_id (String) ID of the KV namespace you want to use.\nNested Schema for placement\nRequired:\nmode (String) The placement mode for the Worker. Available values: smart .\nNested Schema for plain_text_binding\nRequired: name (String) The global variable for the binding in your Worker code.\nservice (String) The name of the Worker to bind to. Optional:\nenvironment (String) The name of the Worker environment to bind to.\nNested Schema for webassembly_binding\nRequired:\nmodule (String) The base64 encoded wasm module you want to store.\nname (String"
      ]
    }
  ],
  "warnings": null,
  "metadata": null,
  "session_id": "ses_f1bfef7dbffeJFSNLNDT39shaW"
}
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.2s)

_Thinking:_



**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://developers.cloudflare.com/d1/worker-api/"
}
```

**Output:**
```
---
description: Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results.
title: Workers Binding API
image: https://developers.cloudflare.com/og-docs.png
---

[Skip to content](#main-content)

> Documentation Index  
> Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt  
> Use this file to discover all available pages before exploring further.

# Workers Binding API

Last updated Apr 21, 2026|Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/d1/worker-api/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

You can execute SQL queries on your D1 database from a Worker using the Worker Binding API. To do this, you can perform the following steps:

1. [Bind the D1 Database](https://developers.cloudflare.com/d1/get-started/#3-bind-your-worker-to-your-d1-database).
2. [Prepare a statement](https://developers.cloudflare.com/d1/worker-api/d1-database/#prepare).
3. [Run the prepared statement](https://developers.cloudflare.com/d1/worker-api/prepared-statements).
4. Analyze the [return object](https://developers.cloudflare.com/d1/worker-api/return-object) (if necessary).

Refer to the relevant sections for the API documentation.

## TypeScript support

D1 Worker Bindings API is fully-typed via the runtime types generated by running [`wrangler types`](https://developers.cloudflare.com/workers/languages/typescript/) package, and also supports [generic types ↗︎](https://www.typescriptlang.org/docs/handbook/2/generics.html#generic-types) as part of its TypeScript API. A generic type allows you to provide an optional `type parameter` so that a function understands the type of the data it is handling.

When using the query statement methods [`D1PreparedStatement::run`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#run), [`D1PreparedStatement::raw`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#raw) and [`D1PreparedStatement::first`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#first), you can provide a type representing each database row. D1's API will [return the result object](https://developers.cloudflare.com/d1/worker-api/return-object/#d1result) with the correct type.

For example, providing an `OrderRow` type as a type parameter to [`D1PreparedStatement::run`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#run) will return a typed `Array<OrderRow>` object instead of the default `Record<string, unknown>` type:

```ts
// Row definition
type OrderRow = {
	Id: string;
	CustomerName: string;
	OrderDate: number;
};

// Elsewhere in your application
// env.MY_DB is the D1 database binding from your Wrangler configuration file
const result = await env.MY_DB.prepare(
	"SELECT Id, CustomerName, OrderDate FROM [Order] ORDER BY ShippedDate DESC LIMIT 100",
).run<OrderRow>();
```

## Type conversion

D1 automatically converts supported JavaScript (including TypeScript) types passed as parameters via the Workers Binding API to their associated D1 types <sup>1</sup>. This conversion is permanent and one-way only. This means that when reading the written values back in your code, you will get the converted values rather than the originally inserted values.

Note

We recommend using [STRICT tables ↗︎](https://www.sqlite.org/stricttables.html) in your SQL schema to avoid issues with mismatched types between values that are actually stored in your database compared to values defined by your schema.

The type conversion during writes is as follows:

| JavaScript (write) | D1 | JavaScript (read) |
| --- | --- | --- |
| null | `NULL` | null |
| Number | `REAL` | Number |
| Number <sup>2</sup> | `INTEGER` | Number |
| String | `TEXT` | String |
| Boolean <sup>3</sup> | `INTEGER` | Number (`0`,`1`) |
| ArrayBuffer | `BLOB` | Array <sup>4</sup> |
| ArrayBuffer View | `BLOB` | Array <sup>4</sup> |
| undefined | Not supported. <sup>5</sup> | - |

<sup>1</sup> D1 types correspond to the underlying [SQLite types ↗︎](https://www.sqlite.org/datatype3.html).

<sup>2</sup> D1 supports 64-bit signed `INTEGER` values internally, however [BigInts ↗︎](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt) are not currently supported in the API yet. JavaScript integers are safe up to [`Number.MAX_SAFE_INTEGER` ↗︎](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER).

<sup>3</sup> Booleans will be cast to an `INTEGER` type where `1` is `TRUE` and `0` is `FALSE`.

<sup>4</sup> `ArrayBuffer` and [`ArrayBuffer` views ↗︎](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer/isView) are converted using [`Array.from` ↗︎](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/from).

<sup>5</sup> Queries with `undefined` values will return a `D1_TYPE_ERROR`.

## API playground

The D1 Worker Binding API playground is an `index.js` file where you can test each of the documented Worker Binding APIs for D1. The file builds from the end-state of the [Get started](https://developers.cloudflare.com/d1/get-started/#write-queries-within-your-worker) code.

You can use this alongside the API documentation to better understand how each API works.

Follow the steps to setup your API playground.

### 1. Complete the Get started tutorial

Complete the [Get started](https://developers.cloudflare.com/d1/get-started/#write-queries-within-your-worker) tutorial. Ensure you use JavaScript instead of TypeScript.

### 2. Modify the content of `index.js`

Replace the contents of your `index.js` file with the code below to view the effect of each API.

<details>

<summary>

index.js

</summary>

```js
// D1 API Playground - Test each D1 Worker Binding API method
// Change the URL pathname to test different methods (e.g., /RUN, /RAW, /FIRST)
export default {
	async fetch(request, env) {
	  const { pathname } = new URL(request.url);

		// Sample data for testing
		const companyName1 = `Bs Beverages`;
		const companyName2 = `Around the Horn`;

		// Prepare reusable statements
		const stmt = env.DB.prepare(`SELECT * FROM Customers WHERE CompanyName = ?`);
		const stmtMulti = env.DB.prepare(`SELECT * FROM Customers; SELECT * FROM Customers WHERE CompanyName = ?`);
		const session = env.DB.withSession("first-primary")
		const sessionStmt = session.prepare(`SELECT * FROM Customers WHERE CompanyName = ?`);

      // Test D1PreparedStatement::run - returns full D1Result object
      if (pathname === `/RUN`){
    	const returnValue = await stmt.bind(companyName1).run();
    	return Response.json(returnValue);

      // Test D1PreparedStatement::raw - returns array of arrays
    } else if (pathname === `/RAW`){
    	const returnValue = await stmt.bind(companyName1).raw();
    	return Response.json(returnValue);

      // Test D1PreparedStatement::first - returns first row only
    } else if (pathname === `/FIRST`){
    	const returnValue = await stmt.bind(companyName1).first();
    	return Response.json(returnValue);

      // Test D1Database::batch - execute multiple statements
    } else if (pathname === `/BATCH`) {
    	const batchResult = await env.DB.batch([
    		stmt.bind(companyName1),
    		stmt.bind(companyName2)
    	]);
    	return Response.json(batchResult);

      // Test D1Database::exec - execute raw SQL without parameters
    } else if (pathname === `/EXEC`){
    	const returnValue = await env.DB.exec(`SELECT * FROM Customers WHERE CompanyName = "Bs Beverages"`);
    	return Response.json(returnValue);

      // Test D1 Sessions API with read replication
    } else if (pathname === `/WITHSESSION`){
    	const returnValue = await sessionStmt.bind(companyName1).run();
    	console.log("You're now using D1 Sessions!")
    	return Response.json(returnValue);
    }

      // Default response with instructions
      return new Response(
    	`Welcome to the D1 API Playground!
    	\nChange the URL to test the various methods inside your index.js file.`,
      );
    },

};
```

</details>

### 3. Deploy the Worker

1. Navigate to your tutorial directory you created by following step 1.
2. Run `npx wrangler deploy`.

   ```sh
   npx wrangler deploy
   ```

   ```sh
   ⛅️ wrangler 3.112.0
   --------------------

   Total Upload: 1.90 KiB / gzip: 0.59 KiB
   Your worker has access to the following bindings:
   - D1 Databases:
   	- DB: DATABASE_NAME (<DATABASE_ID>)
   Uploaded WORKER_NAME (7.01 sec)
   Deployed WORKER_NAME triggers (1.25 sec)
   	https://jun-d1-rr.d1-sandbox.workers.dev
   Current Version ID: VERSION_ID
   ```
3. Open a browser at the specified address.

### 4. Test the APIs

Change the URL to test the various D1 Worker Binding APIs.

```plaintext

```

Was this helpful?

YesNo

## On this page

[![](https://developers.cloudflare.com/_astro/logo.te5VL_aD.svg)Docs](https://developers.cloudflare.com/)

```json
{"@context":"https://schema.org","@type":"WebPage","@id":"https://developers.cloudflare.com/d1/worker-api/#page","headline":"Workers Binding API","description":"Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results.","url":"https://developers.cloudflare.com/d1/worker-api/","inLanguage":"en","image":"https://developers.cloudflare.com/og-docs.png","dateModified":"2026-04-21","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"}}
```

```

**Tool: websearch**

**Input:**
```json
{
  "query": "Cloudflare Workers Python D1 first() to_py dict results example",
  "type": "deep"
}
```

**Output:**
```
{
  "search_id": "search_5502568026b62047b6653671f8107cc0",
  "results": [
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/examples",
      "title": "Python Worker Examples · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "description: Python code examples demonstrating modules, bindings, and SDK usage in Workers. title: Examples image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/workers/llms.txt Use this file to discover all available pages before exploring further.\nExamples\nLast updated Jul 6, 2026|Copy as Markdown|View as Markdown|Agent setup\nCloudflare has a wide range of Python examples in the Workers Example gallery.\nIn addition to those examples, consider the following ones that illustrate Python-specific behavior.\nModules in your Worker\nclass Default(WorkerEntrypoint):\nasync def fetch(self, request):\nbody = await request.json()  # returns a native Python dict\nname = body[\"name\"]\nreturn Response(\"Hello, {name}\".format(name=name))\nReturn a JSON response\nfrom workers import WorkerEntrypoint, Response\nTo use the native Python logging\n```\n    # The default contentType is \"json\"\n    # We can also pass plain text strings\n    await self.env.QUEUE.send(\"hello\", contentType=\"text\")\n    # Send a JSON payload\n    await self.env.QUEUE.send({\"hello\": \"world\"})\n\n    return Response.json({\"write\": \"success\"})\n```\nQuery a D1 Database\nTo use the native Python logging\nfrom workers import WorkerEntrypoint, Response\nTo use the native Python logging\nclass Default(WorkerEntrypoint):\nasync def fetch(self, request):\nresults = await self.env.DB.prepare(\"PRAGMA table_list\").run()\n# Return a JSON response\nreturn Response.json(results)\nTo use the native Python logging\nRefer to Query D1 from Python Workers for a more in-depth tutorial that covers how to create a new D1 database and configure bindings to D1.\nTo use the native Python logging\n```\n    return result.greeting\n```\nTo use the native Python logging\nRefer to the Python Workflows documentation for more information.\nMore Examples\nOr you can clone the examples repository ↗ to explore even more examples:\ngit clone https://github.com/cloudflare/python-workers-examples\nWas this helpful?\nYesNo\nOn this page\nTo use the native Python logging\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/workers/languages/python/examples/#page\",\"headline\":\"Python Worker Examples · Cloudflare Workers docs\",\"description\":\"Python code examples demonstrating modules, bindings, and SDK usage in\nTo use the native Python logging\nWorkers.\",\"url\":\"https://developers.cloudflare.com/workers/languages/python/examples/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-07-06\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"url\":\"https://www.cloudflare.com/\"},\"isPartOf\":{\"@type\":\"WebSi"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api",
      "title": "Workers Binding API · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "description: Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results. title: Workers Binding API image: https://developers.cloudflare.com/og-docs.png\nWhen using the query statement methods D1PreparedStatement::run, D1PreparedStatement::raw and D1PreparedStatement::first, you can provide a type representing each database row. D1's API will return the result object with the correct type.\n```\n  // Test D1PreparedStatement::raw - returns array of arrays\n} else if (pathname === `/RAW`){\n\tconst returnValue = await stmt.bind(companyName1).raw();\n\treturn Response.json(returnValue);\n\n  // Test D1PreparedStatement::first - returns first row only\n} else if (pathname === `/FIRST`){\n```\n```\n\tconst returnValue = await stmt.bind(companyName1).first();\n\treturn Response.json(returnValue);\n\n  // Test D1Database::batch - execute multiple statements\n} else if (pathname === `/BATCH`) {\n\tconst batchResult = await env.DB.batch([\n\t\tstmt.bind(companyName1),\n\t\tstmt.bind(companyName2)\n\t]);\n\treturn Response.json(batchResult);\n\n```\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"WebPage\",\"@id\":\"https://developers.cloudflare.com/d1/worker-api/#page\",\"headline\":\"Workers Binding API · Cloudflare D1 docs\",\"description\":\"Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe\nresults.\",\"url\":\"https://developers.cloudflare.com/d1/worker-api/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-04-21\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"url\":\"https://www.cloudflare.com/\"},\"isPartOf\":{\"@type\":\"WebSite\",\"@id\":\"https://developers.cloudflare.com/#website\",\"name\":"
      ]
    },
    {
      "url": "https://5b04bc4a.preview.developers.cloudflare.com/workers/languages/python/examples/",
      "title": "Python Worker Examples · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "from workers import Responsefrom urllib.parse import urlparse, parse_qsasync def on_fetch(request, env): # Parse the incoming request URL url = urlparse(request.url) # Parse the query parameters into a Python dictionary params = parse_qs(url.query) if \"name\" in params: greeting = \"Hello there, {name}\".format(name=params[\"name\"][0]) return Response(greeting) if url.path == \"/favicon.ico\": return Response(\"\") return Response(\"Hello world!\")\nParse JSON from the incoming request\nfrom workers import Responseasync def on_fetch(request): name = (await request.json()).name return Response(\"Hello, {name}\".format(name=name))\nEmit logs from your Python Worker"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers",
      "title": "Query D1 from Python Workers - Cloudflare Docs",
      "publish_date": null,
      "excerpts": [
        "Query D1 from Python Workers - Cloudflare Docs\nNext steps Refer to Workers Python documentation to learn more about how to use Python in Workers. Review the D1 Workers Binding API and how to query D1 databases. Learn how to import data to your D1 database."
      ]
    },
    {
      "url": "https://5b04bc4a.preview.developers.cloudflare.com/d1/examples/query-d1-from-python-workers/",
      "title": "Query D1 from Python Workers · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "description: Learn how to query D1 from a Python Worker title: Query D1 from Python Workers · Cloudflare D1 docs image: https://developers.cloudflare.com/dev-products-preview.png\nSkip to content\nWas this helpful?\nEdit Issue\nQuery D1 from Python Workers\nLearn how to query D1 from a Python Worker Copy Page The Cloudflare Workers platform supports multiple languages, including TypeScript, JavaScript, Rust and Python. This guide shows you how to query a D1 database from Python and deploy your application globally. Note Support for Python in Cloudflare Workers is in beta. Review the documentation on Python support to understand how Python works within the Workers platform.\nPrerequisites\nBefore getting started, you should:"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python",
      "title": "Write Cloudflare Workers in Python · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "Write Cloudflare Workers in Python · Cloudflare Workers docs\nNext Up Learn more about the basics of Python Workers Learn details about local development, deployment, and how to Python Workers work. Explore the package docs for instructions on how to use packages with Python Workers. Understand which parts of the Python Standard Library are supported in Python Workers."
      ]
    },
    {
      "url": "https://github.com/cloudflare/python-workers-examples",
      "title": "GitHub - cloudflare/python-workers-examples · GitHub",
      "publish_date": null,
      "excerpts": [
        "cloudflare/python-workers-examples\n* Page: GitHub repository\n* URL: https://github.com/cloudflare/python-workers-examples\n* Stars: 307\n* Forks: 69\n* License: Apache-2.0 license\n* Default branch: main\n* Created: 2024-03-28T19:51:35.000Z\n* Commits: 75\nTop-level files\nREADME.md\nPython Workers Examples\nThis is a collection of examples for writing Cloudflare Workers in Python . Use these examples to learn how Python Workers work.\nGet started\n1. git clone https://github.com/cloudflare/python-workers-examples\n2. cd hello\n3. uvx --from workers-py pywrangler dev\n4. Press the b key to open a browser tab, and make a request to your Worker\nYou can run uvx --from workers-py pywrangler dev in any example project directory to run a local development server using Pywrangler , the CLI for Cloudflare Python Workers. This local development server is powered by workerd , the open-source Workers runtime.\nNeed to deploy your Worker to Cloudflare?\n* hello/ — the most basic Python Worker\n* binding/ — shows how bindings work in Python Workers. Put a key into Workers KV, and then read it.\n* fastapi/ — demonstrates how to use the FastAPI package with Python Workers\n* query-d1/ - shows how to query D1 with Python Workers\n* langchain/ — demonstrates how to use the LangChain package with Python Workers. Currently broken.\n* assets/ — An example with an assets binding.\n* durable-objects/ — An example with storing state in a Durable Object .\n* cron/ — shows a simple cron job .\n* workers-ai/ makes a call Workers AI to run inference on Cloudflare's Global Network.\n* image-redraw/ — an example that combines FastAPI , R2 , Queues , Workflows and Workers AI to redraw uploaded images.\n* django/ — runs a naive Django WSGI application directly on Python Workers.\n* django-todo-d1/ — uses Django with D1 for a basic TODO application.\n* fastapi-todo/ — implements the Todo-Backend spec with FastAPI (ASGI) and D1."
      ]
    },
    {
      "url": "https://github.com/cloudflare/workerd/blob/main/types/defines/d1.d.ts",
      "title": "workerd/types/defines/d1.d.ts at main · cloudflare/workerd · GitHub",
      "publish_date": null,
      "excerpts": [
        "cloudflare/workerd — types/defines/d1.d.ts\n* Page: GitHub code file\n* URL: https://github.com/cloudflare/workerd/blob/main/types/defines/d1.d.ts\n* Repository: cloudflare/workerd\n* Path: types/defines/d1.d.ts\n* Ref: main\n* Lines: 108\ninterface D1Meta {\nduration: number;\nsize_after: number;\nrows_read: number;\nrows_written: number;\nlast_row_id: number;\nchanged_db: boolean;\nchanges: number;\n/**\ninterface D1Response {\nsuccess: true;\nmeta: D1Meta & Record<string, unknown>;\nerror?: never;\n}\ntype D1Result<T = unknown> = D1Response & {\nresults: T[];\n};\ninterface D1ExecResult {\ncount: number;\nduration: number;\n}\ntype D1SessionConstraint =\n// Indicates that the first query should go to the primary, and the rest queries\n// using the same D1DatabaseSession will go to any replica that is consistent with\n// the bookmark maintained by the session (returned by the first query).\n| 'first-primary'\n// Indicates that the first query can go anywhere (primary or replica), and the rest queries\n// using the same D1DatabaseSession will go to any replica that is consistent with\n// the bookmark maintained by the session (returned by the first query).\n| 'first-unconstrained';\ntype D1SessionBookmark = string;"
      ]
    },
    {
      "url": "https://github.com/cloudflare/python-workers-examples/blob/main/README.md",
      "title": "python-workers-examples/README.md at main · cloudflare/python-workers-examples · GitHub",
      "publish_date": null,
      "excerpts": [
        "cloudflare/python-workers-examples — README.md\n* Page: GitHub code file\n* URL: https://github.com/cloudflare/python-workers-examples/blob/main/README.md\n* Repository: cloudflare/python-workers-examples\n* Path: README.md\n* Ref: main\n* Lines: 53\nPython Workers Examples\nThis is a collection of examples for writing Cloudflare Workers in Python. Use these examples to learn how Python Workers work.\nGet started\n1. git clone https://github.com/cloudflare/python-workers-examples\n2. cd hello\n3. uvx --from workers-py pywrangler dev\n4. Press the b key to open a browser tab, and make a request to your Worker\nYou can run uvx --from workers-py pywrangler dev in any example project directory to run a local development server using Pywrangler, the CLI for Cloudflare Python Workers. This local development server is powered by workerd, the open-source Workers runtime.\nNeed to deploy your Worker to Cloudflare?\n* hello/ — the most basic Python Worker\n* binding/ — shows how bindings work in Python Workers. Put a key into Workers KV, and then read it.\n* fastapi/ — demonstrates how to use the FastAPI package with Python Workers\n* query-d1/ - shows how to query D1 with Python Workers\n* langchain/ — demonstrates how to use the LangChain package with Python Workers. Currently broken.\n* assets/ — An example with an assets binding.\n* durable-objects/ — An example with storing state in a Durable Object.\n* cron/ — shows a simple cron job.\n* workers-ai/ makes a call Workers AI to run inference on Cloudflare's Global Network.\n* image-redraw/ — an example that combines FastAPI, R2, Queues, Workflows and Workers AI to redraw uploaded images.\n* django/ — runs a naive Django WSGI application directly on Python Workers.\n* django-todo-d1/ — uses Django with D1 for a basic TODO application.\n* fastapi-todo/ — implements the Todo-Backend spec with FastAPI (ASGI) and D1.\n* flask-todo/ — implements the same Todo-Backend API with Flask (WSGI) and D1."
      ]
    },
    {
      "url": "https://deepwiki.com/cloudflare/python-workers-examples/4.4-d1-database-queries",
      "title": "D1 Database Queries | cloudflare/python-workers-examples ...",
      "publish_date": null,
      "excerpts": [
        "D1 Database Queries | cloudflare/python-workers-examples ...\nThis document covers the 04-query-d1 example, which demonstrates integration with Cloudflare D1, a serverless SQL database. This page explains the database schema definition, initialization process using the pywrangler d1 execute command, and querying D1 from Python Workers through environment bindings."
      ]
    }
  ],
  "warnings": null,
  "metadata": null,
  "session_id": "ses_f1bfef7dbffeJFSNLNDT39shaW"
}
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.1s)

**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers"
}
```

**Output:**
```
---
description: Learn how to query D1 from a Python Worker
title: Query D1 from Python Workers
image: https://developers.cloudflare.com/og-docs.png
---

[Skip to content](#main-content)

> Documentation Index  
> Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt  
> Use this file to discover all available pages before exploring further.

# Query D1 from Python Workers

Learn how to query D1 from a Python Worker

Last updated Sep 17, 2026|Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

The Cloudflare Workers platform supports [multiple languages](https://developers.cloudflare.com/workers/languages/), including TypeScript, JavaScript, Rust and Python. This guide shows you how to query a D1 database from [Python](https://developers.cloudflare.com/workers/languages/python/) and deploy your application globally.

## Prerequisites

Before getting started, you should:

1. Review the [D1 tutorial](https://developers.cloudflare.com/d1/get-started/) for TypeScript and JavaScript to learn how to **create a D1 database and configure a Workers project**.
2. Refer to the [Python language guide](https://developers.cloudflare.com/workers/languages/python/) to understand how Python support works on the Workers platform.
3. Have basic familiarity with the Python language.

If you are new to Cloudflare Workers, refer to the [Get started guide](https://developers.cloudflare.com/workers/get-started/guide/) first before continuing with this example.

## Query from Python

This example assumes you have an existing D1 database. To allow your Python Worker to query your database, you first need to create a [binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/) between your Worker and your D1 database and define this in your [Wrangler configuration file](https://developers.cloudflare.com/workers/wrangler/configuration/).

You will need the `database_name` and `database_id` for a D1 database. You can use the `wrangler` CLI to create a new database or fetch the ID for an existing database as follows:

*Create a databasesh*

```sh
npx wrangler d1 create my-first-db
```

*Retrieve a database IDsh*

```sh
npx wrangler d1 info some-existing-db
```

```sh
# ┌───────────────────┬──────────────────────────────────────┐
# │                   │ c89db32e-83f4-4e62-8cd7-7c8f97659029 │
# ├───────────────────┼──────────────────────────────────────┤
# │ name              │ db-enam                              │
# ├───────────────────┼──────────────────────────────────────┤
# │ created_at        │ 2023-06-12T16:52:03.071Z             │
# └───────────────────┴──────────────────────────────────────┘
```

### 1. Configure bindings

In your Wrangler file, create a new `[[d1_databases]]` configuration block and set `database_name` and `database_id` to the name and id (respectively) of the D1 database you want to query:

```jsonc
{
	"$schema": "./node_modules/wrangler/config-schema.json",
	"name": "python-and-d1",
	"main": "src/entry.py",
	"compatibility_flags": [ // Required for Python Workers
		"python_workers"
	],
	// Set this to today's date
	"compatibility_date": "2026-09-26",
	"d1_databases": [
		{
			"binding": "DB", // This will be how you refer to your database in your Worker
			"database_name": "YOUR_DATABASE_NAME",
			"database_id": "YOUR_DATABASE_ID"
		}
	]
}
```

```toml
"$schema" = "./node_modules/wrangler/config-schema.json"
name = "python-and-d1"
main = "src/entry.py"
compatibility_flags = [ "python_workers" ]
# Set this to today's date
compatibility_date = "2026-09-26"

[[d1_databases]]
binding = "DB"
database_name = "YOUR_DATABASE_NAME"
database_id = "YOUR_DATABASE_ID"
```

The value of `binding` is how you will refer to your database from within your Worker. If you change this, you must change this in your Worker script as well.

### 2. Create your Python Worker

To create a Python Worker, create an empty file at `src/entry.py`, matching the value of `main` in your Wrangler file with the contents below:

```python
from workers import Response, WorkerEntrypoint

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Do anything else you'd like on request here!

        try:
            # Query D1 - we'll list all tables in our database in this example
            results = await self.env.DB.prepare("PRAGMA table_list").run()
            # Return a JSON response
            return Response.json(results)
        except Exception as e:
            return Response.json({"error": "Database query failed"}, status=500)
```

The value of `binding` in your Wrangler file exactly must match the name of the variable in your Python code. This example refers to the database via a `DB` binding, and queries this binding via `await self.env.DB.prepare(...)`.

You can then deploy your Python Worker directly:

```sh
npx wrangler deploy
```

```sh
# Example output
#
# Your worker has access to the following bindings:
# - D1 Databases:
#   - DB: db-enam (c89db32e-83f4-4e62-8cd7-7c8f97659029)
# Total Upload: 0.18 KiB / gzip: 0.17 KiB
# Uploaded python-and-d1 (4.93 sec)
# Published python-and-d1 (0.51 sec)
#   https://python-and-d1.YOUR_SUBDOMAIN.workers.dev
# Current Deployment ID: 80b72e19-da82-4465-83a2-c12fb11ccc72
```

Your Worker will be available at `https://python-and-d1.YOUR_SUBDOMAIN.workers.dev`.

If you receive an error deploying:

- Make sure you have configured your [Wrangler configuration file](https://developers.cloudflare.com/workers/wrangler/configuration/) with the `database_id` and `database_name` of a valid D1 database.
- Ensure `compatibility_flags = ["python_workers"]` is set in your [Wrangler configuration file](https://developers.cloudflare.com/workers/wrangler/configuration/), which is required for Python.
- Review the [list of error codes](https://developers.cloudflare.com/workers/observability/errors/), and ensure your code does not throw an uncaught exception.

## Next steps

- Refer to [Workers Python documentation](https://developers.cloudflare.com/workers/languages/python/) to learn more about how to use Python in Workers.
- Review the [D1 Workers Binding API](https://developers.cloudflare.com/d1/worker-api/) and how to query D1 databases.
- Learn [how to import data](https://developers.cloudflare.com/d1/best-practices/import-export-data/) to your D1 database.

Was this helpful?

YesNo

## On this page

[![](https://developers.cloudflare.com/_astro/logo.te5VL_aD.svg)Docs](https://developers.cloudflare.com/)

```json
{"@context":"https://schema.org","@type":"TechArticle","@id":"https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/#page","headline":"Query D1 from Python Workers","description":"Learn how to query D1 from a Python Worker","url":"https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/","inLanguage":"en","image":"https://developers.cloudflare.com/og-docs.png","dateModified":"2026-09-17","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"},"keywords":["Python"]}
```

```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.9s)

_Thinking:_



**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://github.com/cloudflare/python-workers-examples"
}
```

**Output:**
```
                                                                                                               GitHub - cloudflare/python-workers-examples · GitHub                                             

[Skip to content](#start-of-content)     

    

            

## Navigation Menu

[](/)

[Sign in](/login?return_to=https%3A%2F%2Fgithub.com%2Fcloudflare%2Fpython-workers-examples)

Appearance settings

-   Platform
    
    -   AI CODE CREATION
        
        -   [GitHub CopilotWrite better code with AI](https://github.com/features/copilot)
        -   [GitHub Copilot appDirect agents from issue to merge](https://github.com/features/ai/github-app)
        -   [MCP RegistryIntegrate external tools](https://github.com/mcp)
        
    -   DEVELOPER WORKFLOWS
        
        -   [ActionsAutomate any workflow](https://github.com/features/actions)
        -   [CodespacesInstant dev environments](https://github.com/features/codespaces)
        -   [IssuesPlan and track work](https://github.com/features/issues)
        -   [Code ReviewManage code changes](https://github.com/features/code-review)
        -   [Code QualityEnforce quality at merge](https://github.com/features/code-quality)
        
    -   APPLICATION SECURITY
        
        -   [GitHub Advanced SecurityFind and fix vulnerabilities](https://github.com/security/advanced-security)
        -   [Code securitySecure your code as you build](https://github.com/security/advanced-security/code-security)
        -   [Secret protectionStop leaks before they start](https://github.com/security/advanced-security/secret-protection)
        
    -   EXPLORE
        
        -   [Why GitHub](https://github.com/why-github)
        -   [Documentation](https://docs.github.com)
        -   [Blog](https://github.blog)
        -   [Changelog](https://github.blog/changelog)
        -   [Marketplace](https://github.com/marketplace)
        
    
    [View all features](https://github.com/features)
    
-   Solutions
    
    -   BY COMPANY SIZE
        
        -   [Enterprises](https://github.com/enterprise)
        -   [Small and medium teams](https://github.com/team)
        -   [Startups](https://github.com/enterprise/startups)
        -   [Nonprofits](https://github.com/solutions/industry/nonprofits)
        
    -   BY USE CASE
        
        -   [App Modernization](https://github.com/solutions/use-case/app-modernization)
        -   [DevSecOps](https://github.com/solutions/use-case/devsecops)
        -   [DevOps](https://github.com/solutions/use-case/devops)
        -   [CI/CD](https://github.com/solutions/use-case/ci-cd)
        -   [View all use cases](https://github.com/solutions/use-case)
        
    -   BY INDUSTRY
        
        -   [Healthcare](https://github.com/solutions/industry/healthcare)
        -   [Financial services](https://github.com/solutions/industry/financial-services)
        -   [Manufacturing](https://github.com/solutions/industry/manufacturing)
        -   [Government](https://github.com/solutions/industry/government)
        -   [View all industries](https://github.com/solutions/industry)
        
    
    [View all solutions](https://github.com/solutions)
    
-   Resources
    
    -   EXPLORE BY TOPIC
        
        -   [AI](https://github.com/resources/articles?topic=ai)
        -   [Software Development](https://github.com/resources/articles?topic=software-development)
        -   [DevOps](https://github.com/resources/articles?topic=devops)
        -   [Security](https://github.com/resources/articles?topic=security)
        -   [View all topics](https://github.com/resources/articles)
        
    -   EXPLORE BY TYPE
        
        -   [Customer stories](https://github.com/customer-stories)
        -   [Events & webinars](https://github.com/resources/events)
        -   [Ebooks & reports](https://github.com/resources/whitepapers)
        -   [Business insights](https://github.com/solutions/executive-insights)
        -   [GitHub Skills](https://skills.github.com)
        
    -   SUPPORT & SERVICES
        
        -   [Documentation](https://docs.github.com)
        -   [Customer support](https://support.github.com)
        -   [Community forum](https://github.com/orgs/community/discussions)
        -   [Trust center](https://github.com/trust-center)
        -   [Partners](https://github.com/partners)
        
    
    [View all resources](https://github.com/resources)
    
-   Open Source
    
    -   COMMUNITY
        
        -   [GitHub SponsorsFund open source developers](https://github.com/open-source/sponsors)
        
    -   PROGRAMS
        
        -   [Security Lab](https://securitylab.github.com)
        -   [Maintainer Community](https://maintainers.github.com)
        -   [GitHub Stars](https://stars.github.com)
        -   [Archive Program](https://archiveprogram.github.com)
        
    -   REPOSITORIES
        
        -   [Topics](https://github.com/topics)
        -   [Trending](https://github.com/trending)
        -   [Collections](https://github.com/collections)
        
    
-   Enterprise
    
    -   ENTERPRISE SOLUTIONS
        
        -   [Enterprise platformAI-powered developer platform](https://github.com/enterprise)
        
    -   AVAILABLE ADD-ONS
        
        -   [GitHub Advanced SecurityEnterprise-grade security features](https://github.com/security/advanced-security)
        -   [Copilot for BusinessEnterprise-grade AI features](https://github.com/features/copilot/copilot-business)
        -   [Premium SupportEnterprise-grade 24/7 support](https://github.com/enterprise/premium-support)
        
    
-   [Pricing](https://github.com/pricing)

Search/

[Sign in](/login?return_to=https%3A%2F%2Fgithub.com%2Fcloudflare%2Fpython-workers-examples)

[Sign up](/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F%3Cuser-name%3E%2F%3Crepo-name%3E&source=header-repo&source_repo=cloudflare%2Fpython-workers-examples)

Appearance settings

You signed in with another tab or window. Reload to refresh your session. You signed out in another tab or window. Reload to refresh your session. You switched accounts on another tab or window. Reload to refresh your session. Dismiss alert

[cloudflare](/cloudflare) / **[python-workers-examples](/cloudflare/python-workers-examples)** Public

-   [Notifications](/login?return_to=%2Fcloudflare%2Fpython-workers-examples) You must be signed in to change notification settings
-   [Fork 72](/login?return_to=%2Fcloudflare%2Fpython-workers-examples)
-   [Star 334](/login?return_to=%2Fcloudflare%2Fpython-workers-examples)
    

-   [Code](/cloudflare/python-workers-examples)
-   [Issues 10](/cloudflare/python-workers-examples/issues)
-   [Pull requests 14](/cloudflare/python-workers-examples/pulls)
-   [Actions](/cloudflare/python-workers-examples/actions)
-   [Projects](/cloudflare/python-workers-examples/projects)
-   [Security and quality 0](/cloudflare/python-workers-examples/security)
-   [Insights](/cloudflare/python-workers-examples/pulse)

Additional navigation options

-   [Code](/cloudflare/python-workers-examples)
-   [Issues](/cloudflare/python-workers-examples/issues)
-   [Pull requests](/cloudflare/python-workers-examples/pulls)
-   [Actions](/cloudflare/python-workers-examples/actions)
-   [Projects](/cloudflare/python-workers-examples/projects)
-   [Security and quality](/cloudflare/python-workers-examples/security)
-   [Insights](/cloudflare/python-workers-examples/pulse)

 [](/cloudflare/python-workers-examples)

main

[Branches](/cloudflare/python-workers-examples/branches)[Tags](/cloudflare/python-workers-examples/tags)

[](/cloudflare/python-workers-examples/branches)[](/cloudflare/python-workers-examples/tags)

Go to file

Code

Open more actions menu

## Latest commit

## History

[81 Commits](/cloudflare/python-workers-examples/commits/main/)

[](/cloudflare/python-workers-examples/commits/main/)81 Commits

## Folders and files

Name

Name

Last commit message

Last commit date

[.github/workflows](/cloudflare/python-workers-examples/tree/main/.github/workflows "This path skips through empty directories")

[.github/workflows](/cloudflare/python-workers-examples/tree/main/.github/workflows "This path skips through empty directories")

[assets](/cloudflare/python-workers-examples/tree/main/assets "assets")

[assets](/cloudflare/python-workers-examples/tree/main/assets "assets")

[binding](/cloudflare/python-workers-examples/tree/main/binding "binding")

[binding](/cloudflare/python-workers-examples/tree/main/binding "binding")

[chatroom](/cloudflare/python-workers-examples/tree/main/chatroom "chatroom")

[chatroom](/cloudflare/python-workers-examples/tree/main/chatroom "chatroom")

[cron](/cloudflare/python-workers-examples/tree/main/cron "cron")

[cron](/cloudflare/python-workers-examples/tree/main/cron "cron")

[django-markdown-r2](/cloudflare/python-workers-examples/tree/main/django-markdown-r2 "django-markdown-r2")

[django-markdown-r2](/cloudflare/python-workers-examples/tree/main/django-markdown-r2 "django-markdown-r2")

[django-todo-d1](/cloudflare/python-workers-examples/tree/main/django-todo-d1 "django-todo-d1")

[django-todo-d1](/cloudflare/python-workers-examples/tree/main/django-todo-d1 "django-todo-d1")

[django](/cloudflare/python-workers-examples/tree/main/django "django")

[django](/cloudflare/python-workers-examples/tree/main/django "django")

[durable-objects](/cloudflare/python-workers-examples/tree/main/durable-objects "durable-objects")

[durable-objects](/cloudflare/python-workers-examples/tree/main/durable-objects "durable-objects")

[dynamic-py-py](/cloudflare/python-workers-examples/tree/main/dynamic-py-py "dynamic-py-py")

[dynamic-py-py](/cloudflare/python-workers-examples/tree/main/dynamic-py-py "dynamic-py-py")

[fastapi-todo](/cloudflare/python-workers-examples/tree/main/fastapi-todo "fastapi-todo")

[fastapi-todo](/cloudflare/python-workers-examples/tree/main/fastapi-todo "fastapi-todo")

[fastapi](/cloudflare/python-workers-examples/tree/main/fastapi "fastapi")

[fastapi](/cloudflare/python-workers-examples/tree/main/fastapi "fastapi")

[flask-todo](/cloudflare/python-workers-examples/tree/main/flask-todo "flask-todo")

[flask-todo](/cloudflare/python-workers-examples/tree/main/flask-todo "flask-todo")

[hello](/cloudflare/python-workers-examples/tree/main/hello "hello")

[hello](/cloudflare/python-workers-examples/tree/main/hello "hello")

[hyperdrive-batched-counter](/cloudflare/python-workers-examples/tree/main/hyperdrive-batched-counter "hyperdrive-batched-counter")

[hyperdrive-batched-counter](/cloudflare/python-workers-examples/tree/main/hyperdrive-batched-counter "hyperdrive-batched-counter")

[image-gen](/cloudflare/python-workers-examples/tree/main/image-gen "image-gen")

[image-gen](/cloudflare/python-workers-examples/tree/main/image-gen "image-gen")

[image-redraw](/cloudflare/python-workers-examples/tree/main/image-redraw "image-redraw")

[image-redraw](/cloudflare/python-workers-examples/tree/main/image-redraw "image-redraw")

[js-api-pygments](/cloudflare/python-workers-examples/tree/main/js-api-pygments "js-api-pygments")

[js-api-pygments](/cloudflare/python-workers-examples/tree/main/js-api-pygments "js-api-pygments")

[langchain](/cloudflare/python-workers-examples/tree/main/langchain "langchain")

[langchain](/cloudflare/python-workers-examples/tree/main/langchain "langchain")

[mcp-server](/cloudflare/python-workers-examples/tree/main/mcp-server "mcp-server")

[mcp-server](/cloudflare/python-workers-examples/tree/main/mcp-server "mcp-server")

[opengraph](/cloudflare/python-workers-examples/tree/main/opengraph "opengraph")

[opengraph](/cloudflare/python-workers-examples/tree/main/opengraph "opengraph")

[query-d1](/cloudflare/python-workers-examples/tree/main/query-d1 "query-d1")

[query-d1](/cloudflare/python-workers-examples/tree/main/query-d1 "query-d1")

[sync-http-clients](/cloudflare/python-workers-examples/tree/main/sync-http-clients "sync-http-clients")

[sync-http-clients](/cloudflare/python-workers-examples/tree/main/sync-http-clients "sync-http-clients")

[tests](/cloudflare/python-workers-examples/tree/main/tests "tests")

[tests](/cloudflare/python-workers-examples/tree/main/tests "tests")

[url-shortener](/cloudflare/python-workers-examples/tree/main/url-shortener "url-shortener")

[url-shortener](/cloudflare/python-workers-examples/tree/main/url-shortener "url-shortener")

[vectorize-rag](/cloudflare/python-workers-examples/tree/main/vectorize-rag "vectorize-rag")

[vectorize-rag](/cloudflare/python-workers-examples/tree/main/vectorize-rag "vectorize-rag")

[websocket-stream-consumer](/cloudflare/python-workers-examples/tree/main/websocket-stream-consumer "websocket-stream-consumer")

[websocket-stream-consumer](/cloudflare/python-workers-examples/tree/main/websocket-stream-consumer "websocket-stream-consumer")

[workers-ai](/cloudflare/python-workers-examples/tree/main/workers-ai "workers-ai")

[workers-ai](/cloudflare/python-workers-examples/tree/main/workers-ai "workers-ai")

[workflows](/cloudflare/python-workers-examples/tree/main/workflows "workflows")

[workflows](/cloudflare/python-workers-examples/tree/main/workflows "workflows")

[.gitignore](/cloudflare/python-workers-examples/blob/main/.gitignore ".gitignore")

[.gitignore](/cloudflare/python-workers-examples/blob/main/.gitignore ".gitignore")

[.pre-commit-config.yaml](/cloudflare/python-workers-examples/blob/main/.pre-commit-config.yaml ".pre-commit-config.yaml")

[.pre-commit-config.yaml](/cloudflare/python-workers-examples/blob/main/.pre-commit-config.yaml ".pre-commit-config.yaml")

[LICENSE.md](/cloudflare/python-workers-examples/blob/main/LICENSE.md "LICENSE.md")

[LICENSE.md](/cloudflare/python-workers-examples/blob/main/LICENSE.md "LICENSE.md")

[README.md](/cloudflare/python-workers-examples/blob/main/README.md "README.md")

[README.md](/cloudflare/python-workers-examples/blob/main/README.md "README.md")

[pyproject.toml](/cloudflare/python-workers-examples/blob/main/pyproject.toml "pyproject.toml")

[pyproject.toml](/cloudflare/python-workers-examples/blob/main/pyproject.toml "pyproject.toml")

[uv.lock](/cloudflare/python-workers-examples/blob/main/uv.lock "uv.lock")

[uv.lock](/cloudflare/python-workers-examples/blob/main/uv.lock "uv.lock")

View all files

## Repository files navigation

-   [README](#)
-   [Code of conduct](#)
-   [Contributing](#)
-   [Apache-2.0 license](#)
-   [Security](#)

More items

# Python Workers Examples

[](#python-workers-examples)

This is a collection of examples for [writing Cloudflare Workers in Python](https://developers.cloudflare.com/workers/languages/python). Use these examples to learn how Python Workers work.

## Get started

[](#get-started)

1.  `git clone https://github.com/cloudflare/python-workers-examples`
2.  `cd hello`
3.  `uvx --from workers-py pywrangler dev`
4.  Press the `b` key to open a browser tab, and make a request to your Worker

You can run `uvx --from workers-py pywrangler dev` in any example project directory to run a local development server using [Pywrangler](https://github.com/cloudflare/workers-py), the CLI for Cloudflare Python Workers. This local development server is powered by [workerd](https://github.com/cloudflare/workerd), the open-source Workers runtime.

Need to deploy your Worker to Cloudflare? Python Workers are in open beta and have a few [limitations](#open-beta-and-limits).

## Examples

[](#examples)

-   [**`hello/`**](/cloudflare/python-workers-examples/blob/main/hello) — the most basic Python Worker
-   [**`binding/`**](/cloudflare/python-workers-examples/blob/main/binding) — shows how [bindings](https://developers.cloudflare.com/workers/configuration/bindings/) work in Python Workers. Put a key into Workers KV, and then read it.
-   [**`fastapi/`**](/cloudflare/python-workers-examples/blob/main/fastapi) — demonstrates how to use the [FastAPI](https://fastapi.tiangolo.com/) package with Python Workers
-   [**`query-d1/`**](/cloudflare/python-workers-examples/blob/main/query-d1) - shows how to query D1 with Python Workers
-   [**`mcp-server/`**](/cloudflare/python-workers-examples/blob/main/mcp-server) — an MCP server backed by D1.
-   [**`langchain/`**](/cloudflare/python-workers-examples/blob/main/langchain) — demonstrates how to use the [LangChain](https://pypi.org/project/langchain/) package with Python Workers. Currently broken.
-   [**`assets/`**](/cloudflare/python-workers-examples/blob/main/assets) — An example with an assets binding.
-   [**`durable-objects/`**](/cloudflare/python-workers-examples/blob/main/durable-objects) — An example with storing state in a [Durable Object](https://developers.cloudflare.com/durable-objects/).
-   [**`hyperdrive-batched-counter/`**](/cloudflare/python-workers-examples/blob/main/hyperdrive-batched-counter) — batches high-frequency counters with Durable Objects and PostgreSQL through Hyperdrive.
-   [**`cron/`**](/cloudflare/python-workers-examples/blob/main/cron) — shows a simple [cron job](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
-   [**`workers-ai/`**](/cloudflare/python-workers-examples/blob/main/workers-ai) makes a call [Workers AI](https://developers.cloudflare.com/workers-ai/) to run inference on Cloudflare's Global Network.
-   [**`vectorize-rag/`**](/cloudflare/python-workers-examples/blob/main/vectorize-rag) — a RAG example using remote Workers AI and [Vectorize](https://developers.cloudflare.com/vectorize/) bindings.
-   [**`workflows/`**](/cloudflare/python-workers-examples/blob/main/workflows) — shows a durable [Workflows](https://developers.cloudflare.com/workflows/) example.
-   [**`opengraph/`**](/cloudflare/python-workers-examples/blob/main/opengraph) — shows how to use [HTMLRewriter](https://developers.cloudflare.com/workers/runtime-apis/html-rewriter/) to generate OpenGraph images with Python Workers.
-   [**`image-gen/`**](/cloudflare/python-workers-examples/blob/main/image-gen) — shows how to use [Pillow](https://pillow.readthedocs.io/en/stable/) to generate images with Python Workers.
-   [**`js-api-pygments/`**](/cloudflare/python-workers-examples/blob/main/js-api-pygments) — shows how to use [Pygments](https://pygments.org/) to highlight code with Python Workers.
-   [**`websocket-stream-consumer/`**](/cloudflare/python-workers-examples/blob/main/websocket-stream-consumer) — shows how to use [WebSocket](https://developers.cloudflare.com/workers/runtime-apis/websockets/) to consume a stream of data with Python Workers.
-   [**`chatroom/`**](/cloudflare/python-workers-examples/blob/main/chatroom) - A real-time chatroom using WebSocket.
-   [**`sync-http-clients/`**](/cloudflare/python-workers-examples/blob/main/sync-http-clients) — demonstrates outbound HTTP with synchronous Python clients (`requests`, `urllib3`, and `httpx.Client`).
-   [**`url-shortener/`**](/cloudflare/python-workers-examples/blob/main/url-shortener) — a URL shortener backed by Workers KV.
-   [**`dynamic-py-py/`**](/cloudflare/python-workers-examples/blob/main/dynamic-py-py) — shows how to load and run a Python Worker dynamically at runtime using a [Worker Loader](https://developers.cloudflare.com/workers/runtime-apis/bindings/worker-loader/) binding.
-   [**`image-redraw/`**](/cloudflare/python-workers-examples/blob/main/image-redraw) — an example that combines [FastAPI](https://fastapi.tiangolo.com/), [R2](https://developers.cloudflare.com/r2/), [Queues](https://developers.cloudflare.com/queues/), [Workflows](https://developers.cloudflare.com/workflows/) and [Workers AI](https://developers.cloudflare.com/workers-ai/) to redraw uploaded images.
-   [**`django/`**](/cloudflare/python-workers-examples/blob/main/django) — runs a naive Django WSGI application directly on Python Workers.
-   [**`django-todo-d1/`**](/cloudflare/python-workers-examples/blob/main/django-todo-d1) — uses Django with D1 for a basic TODO application.
-   [**`django-markdown-r2/`**](/cloudflare/python-workers-examples/blob/main/django-markdown-r2) — a server-rendered Django blog using Durable Object SQLite and R2 for media storage.
-   [**`fastapi-todo/`**](/cloudflare/python-workers-examples/blob/main/fastapi-todo) — implements the [Todo-Backend](https://todobackend.com) spec with FastAPI (ASGI) and D1.
-   [**`flask-todo/`**](/cloudflare/python-workers-examples/blob/main/flask-todo) — implements the same [Todo-Backend](https://todobackend.com) API with [Flask](https://flask.palletsprojects.com/) (WSGI) and D1.

## Open Beta and Limits

[](#open-beta-and-limits)

-   You must add the `python_workers` compatibility flag to your Worker while Python Workers are in open beta.

We’d love your feedback. Join the `#python-workers channel` in the [Cloudflare Developers Discord](https://discord.cloudflare.com/) and let us know what you’d like to see next.

## License

[](#license)

The [Apache 2.0 license](/cloudflare/python-workers-examples/blob/main/LICENSE.md).

## About

No description, website, or topics provided.

### Resources

[Readme](#readme-ov-file)

[Apache-2.0 license](#Apache-2.0-1-ov-file)

### Code of conduct

[Code of conduct](/cloudflare/python-workers-examples#coc-ov-file)

### Contributing

[Contributing](#contributing-ov-file)

### Security policy

[Security policy](#security-ov-file)

[Activity](/cloudflare/python-workers-examples/activity)

[Custom properties](/cloudflare/python-workers-examples/custom-properties)

### Stars

**334** stars

### Watchers

**17** watching

### Forks

[**72** forks](/cloudflare/python-workers-examples/forks)

[Report repository](/contact/report-content?content_url=https%3A%2F%2Fgithub.com%2Fcloudflare%2Fpython-workers-examples&report=cloudflare+%28user%29)

## Releases

## Packages

## Used by

## Contributors

## Languages

## Footer

[](https://github.com)© 2026 GitHub, Inc.

### Footer navigation

-   [Terms](https://docs.github.com/site-policy/github-terms/github-terms-of-service)
-   [Privacy](https://docs.github.com/site-policy/privacy-policies/github-privacy-statement)
-   [Security](https://github.com/security)
-   [Status](https://www.githubstatus.com/)
-   [Community](https://github.community/)
-   [Docs](https://docs.github.com/)
-   [Contact](https://support.github.com?tags=dotcom-footer)
-   Manage cookies
-   Do not share my personal information

You can’t perform that action at this time.
```

**Tool: websearch**

**Input:**
```json
{
  "query": "site:developers.cloudflare.com python workers D1 to_py results.first all",
  "type": "deep"
}
```

**Output:**
```
{
  "search_id": "search_200f5bf195a433c772d035535e0df253",
  "results": [
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/how-python-workers-work",
      "title": "How Python Workers Work - Cloudflare Docs",
      "publish_date": null,
      "excerpts": [
        "description: Learn how Python Workers run via Pyodide in V8 isolates and how local development works. title: How Python Workers Work image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/workers/llms.txt Use this file to discover all available pages before exploring further.\nHow Python Workers Work\nLast updated Jul 9, 2026|Copy as Markdown|View as Markdown|Agent setup\nWorkers written in Python are executed by Pyodide ↗. Pyodide is a CPython ↗ (the reference implementation of Python — commonly referred to as just \"Python\") compiled to WebAssembly.\nWhen you write a Python Worker, your code is interpreted directly by Pyodide, within a V8 isolate. Refer to How Workers works to learn more.\nLocal Development\nA basic Python Worker includes a Python file with a Default class extending WorkerEntrypoint, such as:\nfrom workers import Response, WorkerEntrypoint\n\"$schema\" = \"./node_modules/wrangler/config-schema.json\"\nname = \"hello-world-python-worker\"\nmain = \"src/entry.py\"\nSet this to today's date\nThere are no extra toolchain or precompilation steps needed. The Python execution environment is provided directly by the Workers runtime, mirroring how Workers written in JavaScript work.\nRefer to the Python examples to learn how to use Python within Workers.\nSet this to today's date\n1. Wrangler uploads your Python code and any packages included in your pyproject.toml to the Workers API.\n2. Cloudflare sends your Python code to the Workers runtime to be validated.\n3. Cloudflare creates a new v8 isolate for your Worker, automatically injecting Pyodide.\n4.\nSet this to today's date\nCloudflare deploys this snapshot alongside your Worker’s Python code to the Cloudflare network.\nWhen a request comes in to your Worker, we load this snapshot and use it to bootstrap your Worker in an isolate, avoiding expensive initialization time:\n<Diagram of how Python Workers are deployed to Cloudflare>\nSet this to today's date\nRefer to the blog post introducing Python Workers ↗ for more detail about performance optimizations and how the Workers runtime will reduce cold starts for Python Workers.\nSet this to today's date\nFollowing the Workers Runtime policy to never break an application that is live in production, existing Python Workers on versions outside the support window will continue to work.\nSet this to today's date\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/#page\",\"headline\":\"How Python Workers Work · Cloudflare Workers docs\",\"description\":\"Learn how Python Workers run via Pyodide in V8 isolates and how local development"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/",
      "title": "Query D1 from Python Workers - Cloudflare Docs",
      "publish_date": null,
      "excerpts": [
        "Section: Return a JSON response\nDocs {\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/#page\",\"headline\":\"Query D1 from Python Workers\",\"description\":\"Learn how to query D1 from a Python Worker\",\"url\":\"https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-09-17\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"description\":\"One platform for your apps, agents, and workforce."
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python",
      "title": "Write Cloudflare Workers in Python · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "* Easy to install and fast-booting Packages, including FastAPI ↗, Langchain ↗, Pydantic ↗ and more.\n* A robust foreign function interface (FFI) that lets you use JavaScript objects and functions directly from Python — including all Runtime APIs\n* An ecosystem of services on the Workers Platform accessible via bindings, including:\n* State storage and databases like KV, D1, Durable Objects\n* Access to Environment Variables, Secrets, and other Workers using Service Bindings\n* AI capabilities with Workers AI, Vectorize\n* File storage with R2\n* Durable Workflows, Queues, and more"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api/index.md",
      "title": "Workers Binding API",
      "publish_date": null,
      "excerpts": [
        "description: Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe results. title: Workers Binding API image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt Use this file to discover all available pages before exploring further.\nWorkers Binding API\nLast updated Apr 21, 2026|Copy as Markdown|View as Markdown|Agent setup\nYou can execute SQL queries on your D1 database from a Worker using the Worker Binding API. To do this, you can perform the following steps:\nD1 Worker Bindings API is fully-typed via the runtime types generated by running wrangler types package, and also supports generic types ↗ as part of its TypeScript API. A generic type allows you to provide an optional type parameter so that a function understands the type of the data it is handling.\nD1 automatically converts supported JavaScript (including TypeScript) types passed as parameters via the Workers Binding API to their associated D1 types 1. This conversion is permanent and one-way only. This means that when reading the written values back in your code, you will get the converted values rather than the originally inserted values.\nAPI playground\nThe D1 Worker Binding API playground is an index.js file where you can test each of the documented Worker Binding APIs for D1. The file builds from the end-state of the Get started code.\nYou can use this alongside the API documentation to better understand how each API works.\nFollow the steps to setup your API playground.\nReplace the contents of your index.js file with the code below to view the effect of each API.\nindex.js\n// D1 API Playground - Test each D1 Worker Binding API method\n// Change the URL pathname to test different methods (e.g., /RUN, /RAW, /FIRST)\nexport default {\nasync fetch(request, env) {\nconst { pathname } = new URL(request.url);\n```\n  // Test D1PreparedStatement::raw - returns array of arrays\n} else if (pathname === `/RAW`){\n\tconst returnValue = await stmt.bind(companyName1).raw();\n\treturn Response.json(returnValue);\n\n  // Test D1PreparedStatement::first - returns first row only\n} else if (pathname === `/FIRST`){\n```\n- D1 Databases:\n  - DB: DATABASE_NAME (<DATABASE_ID>)\n    Uploaded WORKER_NAME (7.01 sec)\n    Deployed WORKER_NAME triggers (1.25 sec)\n    https://jun-d1-rr.d1-sandbox.workers.dev\n    Current Version ID: VERSION_ID\n3. Open a browser at the specified address.\n4. Test the APIs\nChange the URL to test the various D1 Worker Binding APIs.\nWas this helpful?\nYesNo\nOn this page\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"WebPage\",\"@id\":\"https://developers.cloudflare.com/d1/worker-api/#page\",\"headline\":\"Workers Binding API · Cloudflare D1 docs\",\"description\":\"Query D1 databases from a Cloudflare Worker using the D1 Binding API for prepared statements, batching, and type-safe"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/stdlib",
      "title": "Standard Library provided to Python Workers",
      "publish_date": null,
      "excerpts": [
        "description: Python standard library availability and limitations in Cloudflare Workers. title: Standard Library image: https://developers.cloudflare.com/og-docs.png\nLast updated Jun 22, 2026|Copy as Markdown|View as Markdown|Agent setup\nWorkers written in Python are executed by Pyodide ↗.\nPyodide is a port of CPython to WebAssembly — for the most part it behaves identically to CPython ↗ (the reference implementation of Python — commonly referred to as just \"Python\").\nThe majority of the CPython test suite passes when run against Pyodide. For the most part, you shouldn't need to worry about differences in behavior.\nThe full Python Standard Library ↗ is available in Python Workers, with the following exceptions:\nExcluded modules\nThe following modules are not available in Python Workers:\nPython Workers have access to an ephemeral, in-memory filesystem. You can read and write files using standard Python file I/O (for example, open(), pathlib.Path), but all data is lost when the Worker isolate is destroyed. The filesystem is not shared between different isolate instances.\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/workers/languages/python/stdlib/#page\",\"headline\":\"Standard Library provided to Python Workers · Cloudflare Workers docs\",\"description\":\"Python standard library availability and limitations in Cloudflare\nWorkers.\",\"url\":\"https://developers.cloudflare.com/workers/languages/python/stdlib/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-06-22\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"url\":\"https://www.cloudflare.com/\"},\"isPartOf\":{\"@type\":\"WebSite\",\"@id\":\"https://developers.cloudflare.com"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api/prepared-statements",
      "title": "Prepared statement methods · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "Prepared statement methods · Cloudflare D1 docs\nJun 22, 2026 — Bind parameters and run D1 prepared statements using the run, all, first, and raw methods. D1 from Python Workers Tutorials. This chapter"
      ]
    },
    {
      "url": "https://5b04bc4a.preview.developers.cloudflare.com/d1/examples/query-d1-from-python-workers/",
      "title": "Query D1 from Python Workers · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "description: Learn how to query D1 from a Python Worker title: Query D1 from Python Workers · Cloudflare D1 docs image: https://developers.cloudflare.com/dev-products-preview.png\nSkip to content\nWas this helpful?\nEdit Issue\nQuery D1 from Python Workers\nLearn how to query D1 from a Python Worker Copy Page The Cloudflare Workers platform supports multiple languages, including TypeScript, JavaScript, Rust and Python. This guide shows you how to query a D1 database from Python and deploy your application globally. Note Support for Python in Cloudflare Workers is in beta. Review the documentation on Python support to understand how Python works within the Workers platform.\nPrerequisites\nBefore getting started, you should:"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api",
      "title": "Workers Binding API · Cloudflare D1 docs",
      "publish_date": null,
      "excerpts": [
        "Workers Binding API · Cloudflare D1 docs\nApr 21, 2026 — Worker using the D1 Binding API for prepared statements, batching, and type-safe results. Prepare a statement. Run the prepared statement."
      ]
    },
    {
      "url": "https://developers.cloudflare.com/d1/worker-api/d1-database",
      "title": "D1 Database",
      "publish_date": null,
      "excerpts": [
        "D1 Database\nLocal development ... To send batch statements, provide D1Database::batch a list of prepared statements and get the results in the same order."
      ]
    },
    {
      "url": "https://9a798b9b.previews.developers.cloudflare.com/workers/languages/python/index.md",
      "title": "Python Workers",
      "publish_date": null,
      "excerpts": [
        "When you initialize a new Python Worker project and select from one of many templates: uv run pywrangler init Or you can clone the examples repository to explore more options: git clone https://github.com/cloudflare/python-workers-examples cd python-workers-examples/hello\nNext Up\nLearn more about the basics of Python Workers\nLearn details about local development, deployment, and how to Python Workers work.\nExplore the package docs for instructions on how to use packages with Python Workers.\nUnderstand which parts of the Python Standard Library are supported in Python Workers.\nLearn about Python Workers' foreign function interface (FFI), and how to use it to work with bindings and Runtime APIs. Was this helpful? YesNo\nOn this page"
      ]
    }
  ],
  "warnings": null,
  "metadata": null,
  "session_id": "ses_f1bfef7dbffeJFSNLNDT39shaW"
}
```

---

## Assistant (Build · Muse Spark 1.3 Free · 7.0s)

_Thinking:_



**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://developers.cloudflare.com/d1/worker-api/prepared-statements"
}
```

**Output:**
```
---
description: Bind parameters and run D1 prepared statements using the run, all, first, and raw methods.
title: Prepared statement methods
image: https://developers.cloudflare.com/og-docs.png
---

[Skip to content](#main-content)

> Documentation Index  
> Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt  
> Use this file to discover all available pages before exploring further.

# Prepared statement methods

Last updated Jun 22, 2026|Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/d1/worker-api/prepared-statements/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

This chapter documents the various ways you can run and retrieve the results of a query after you have [prepared your statement](https://developers.cloudflare.com/d1/worker-api/d1-database/#prepare).

## Methods

### `bind()`

Binds a parameter to the prepared statement.

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
```

```py
some_variable = "Bs Beverages"
stmt = self.env.DB.prepare(
  "SELECT * FROM Customers WHERE CompanyName = ?"
).bind(some_variable)
```

#### Parameter

- `Variable`: `string`
  - The variable to be appended into the prepared statement. See [guidance](#guidance) below.

#### Return values

- `D1PreparedStatement`: `Object`
  - A `D1PreparedStatement` where the input parameter has been included in the statement.

#### Guidance

- D1 follows the [SQLite convention ↗︎](https://www.sqlite.org/lang_expr.html#varparam) for prepared statements parameter binding. Currently, D1 only supports Ordered ( `?NNNN`) and Anonymous ( `?`) parameters. In the future, D1 will support named parameters as well.

  | Syntax | Type | Description |
  | --- | --- | --- |
  | `?NNN` | Ordered | A question mark followed by a number `NNN` holds a spot for the `NNN`-th parameter. `NNN` must be between `1` and `SQLITE_MAX_VARIABLE_NUMBER` |
  | `?` | Anonymous | A question mark that is not followed by a number creates a parameter with a number one greater than the largest parameter number already assigned. If this means the parameter number is greater than `SQLITE_MAX_VARIABLE_NUMBER`, it is an error. This parameter format is provided for compatibility with other database engines. But because it is easy to miscount the question marks, the use of this parameter format is discouraged. Programmers are encouraged to use one of the symbolic formats below or the `?NNN` format above instead. |

  To bind a parameter, use the `.bind` method.

  Order and anonymous examples:

  ```js
  const stmt = db.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind("");
  ```

  ```py
  stmt = db.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind("")
  ```

  ```js
  const stmt = db
  	.prepare("SELECT * FROM Customers WHERE CompanyName = ? AND CustomerId = ?")
  	.bind("Alfreds Futterkiste", 1);
  ```

  ```py
  stmt = db.prepare(
  "SELECT * FROM Customers WHERE CompanyName = ? AND CustomerId = ?"
  ).bind("Alfreds Futterkiste", 1)
  ```

  ```js
  const stmt = db
  	.prepare(
    "SELECT * FROM Customers WHERE CompanyName = ?2 AND CustomerId = ?1"
  ).bind(1, "Alfreds Futterkiste");
  ```

  ```py
  stmt = db.prepare("SELECT * FROM Customers WHERE CompanyName = ?2 AND CustomerId = ?1").bind(1, "Alfreds Futterkiste")
  ```



#### Static statements

D1 API supports static statements. Static statements are SQL statements where the variables have been hard coded. When writing a static statement, you manually type the variable within the statement string.

Advantages of prepared statements

The recommended approach is to use [prepared statements](https://developers.cloudflare.com/d1/worker-api/d1-database/#prepare) to run the SQL and bind parameters to them. Binding parameters using [`bind()`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#bind) to prepared statements allows you to reuse the prepared statements in your code, and prevents SQL injection attacks.

Example of a prepared statement with dynamically bound value:

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
// A variable (someVariable) will replace the placeholder '?' in the query.
// `stmt` is a prepared statement.
```

```py
some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
# A variable (some_variable) will replace the placeholder '?' in the query.
# `stmt` is a prepared statement.
```

Example of a static statement:

```js
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = 'Bs Beverages'");
// "Bs Beverages" is hard-coded into the query.
// `stmt` is a static statement.
```

```py
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = 'Bs Beverages'")
# "Bs Beverages" is hard-coded into the query.
# `stmt` is a static statement.
```

### `run()`

Runs the prepared query (or queries) and returns results. The returned results includes metadata.

```js
const returnValue = await stmt.run();
```

```py
return_value = await stmt.run()
```

#### Parameter

- None.

#### Return values

- `D1Result`: `Object`
  - An object containing the success status, a meta object, and an array of objects containing the query results.
  - For more information on the object, refer to [`D1Result`](https://developers.cloudflare.com/d1/worker-api/return-object/#d1result).

<details>

<summary>

Example of return values

</summary>

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.run();
return Response.json(returnValue);
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.run()
return Response.json(return_value)
```

```json
{
  "success": true,
  "meta": {
    "served_by": "miniflare.db",
    "duration": 1,
    "changes": 0,
    "last_row_id": 0,
    "changed_db": false,
    "size_after": 8192,
    "rows_read": 4,
    "rows_written": 0
  },
  "results": [
    {
      "CustomerId": 11,
      "CompanyName": "Bs Beverages",
      "ContactName": "Victoria Ashworth"
    },
    {
      "CustomerId": 13,
      "CompanyName": "Bs Beverages",
      "ContactName": "Random Name"
    }
  ]
}
```

</details>

#### Guidance

- `results` is empty for write operations such as `UPDATE`, `DELETE`, or `INSERT`.
- When using TypeScript, you can pass a [type parameter](https://developers.cloudflare.com/d1/worker-api/#typescript-support) to [`D1PreparedStatement::run`](#run) to return a typed result object.
- [`D1PreparedStatement::run`](#run) is functionally equivalent to `D1PreparedStatement::all`, and can be treated as an alias.
- You can choose to extract only the results you expect from the statement by simply returning the `results` property of the return object.

<details>

<summary>

Example of returning only the <code>results</code>

</summary>

```js
return Response.json(returnValue.results);
```

```py
from workers import Response

return Response.json(return_value.results)
```

```json
[
  {
    "CustomerId": 11,
    "CompanyName": "Bs Beverages",
    "ContactName": "Victoria Ashworth"
  },
  {
    "CustomerId": 13,
    "CompanyName": "Bs Beverages",
    "ContactName": "Random Name"
  }
]
```

</details>

### `raw()`

Runs the prepared query (or queries), and returns the results as an array of arrays. The returned results do not include metadata.

Column names are not included in the result set by default. To include column names as the first row of the result array, set `.raw({columnNames: true})`.

```js
const returnValue = await stmt.raw();
```

```py
return_value = await stmt.raw()
```

#### Parameters

- `columnNames`: `Object` Optional
  - A boolean object which includes column names as the first row of the result array.

#### Return values

- `Array`: `Array`
  - An array of arrays. Each sub-array represents a row.

<details>

<summary>

Example of return values

</summary>

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.raw();
return Response.json(returnValue);
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.raw()
return Response.json(return_value)
```

```json
[
  [11, "Bs Beverages",
    "Victoria Ashworth"
  ],
  [13, "Bs Beverages",
    "Random Name"
  ]
]
```

With parameter <code>columnNames: true</code>:

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.raw({columnNames:true});
return Response.json(returnValue)
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.raw(columnNames=True)
return Response.json(return_value)
```

```json
[
  [
    "CustomerId",
    "CompanyName",
    "ContactName"
  ],
  [11, "Bs Beverages",
    "Victoria Ashworth"
  ],
  [13, "Bs Beverages",
    "Random Name"
  ]
]
```

</details>

#### Guidance

- When using TypeScript, you can pass a [type parameter](https://developers.cloudflare.com/d1/worker-api/#typescript-support) to [`D1PreparedStatement::raw`](#raw) to return a typed result array.

### `first()`

Runs the prepared query (or queries), and returns the first row of the query result as an object. This does not return any metadata. Instead, it directly returns the object.

```js
const values = await stmt.first();
```

```py
values = await stmt.first()
```

#### Parameters

- `columnName`: `String` Optional
  - Specify a `columnName` to return a value from a specific column in the first row of the query result.
- None.
  - Do not pass a parameter to obtain all columns from the first row.

#### Return values

- `firstRow`: `Object` Optional
  - An object containing the first row of the query result.
  - The return value will be further filtered to a specific attribute if `columnName` was specified.
- `null`: `null`
  - If the query returns no rows.

<details>

<summary>

Example of return values

</summary>

Get all the columns from the first row:

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.first();
return Response.json(returnValue)
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.first()
return Response.json(return_value)
```

```json
{
  "CustomerId": 11,
  "CompanyName": "Bs Beverages",
  "ContactName": "Victoria Ashworth"
}
```

Get a specific column from the first row:

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.first("CustomerId");
return Response.json(returnValue)
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.first("CustomerId")
return Response.json(return_value)
```

```json
11
```

</details>

#### Guidance

- If the query returns rows but `column` does not exist, then [`D1PreparedStatement::first`](#first) throws the `D1_ERROR` exception.
- [`D1PreparedStatement::first`](#first) does not alter the SQL query. To improve performance, consider appending `LIMIT 1` to your statement.
- When using TypeScript, you can pass a [type parameter](https://developers.cloudflare.com/d1/worker-api/#typescript-support) to [`D1PreparedStatement::first`](#first) to return a typed result object.

Was this helpful?

YesNo

## On this page

[![](https://developers.cloudflare.com/_astro/logo.te5VL_aD.svg)Docs](https://developers.cloudflare.com/)

```json
{"@context":"https://schema.org","@type":"TechArticle","@id":"https://developers.cloudflare.com/d1/worker-api/prepared-statements/#page","headline":"Prepared statement methods","description":"Bind parameters and run D1 prepared statements using the run, all, first, and raw methods.","url":"https://developers.cloudflare.com/d1/worker-api/prepared-statements/","inLanguage":"en","image":"https://developers.cloudflare.com/og-docs.png","dateModified":"2026-06-22","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"}}
```

```

**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://developers.cloudflare.com/d1/worker-api/return-object"
}
```

**Output:**
```
---
description: Understand the D1Result and D1ExecResult objects returned by D1 Worker Binding API query methods.
title: Return objects
image: https://developers.cloudflare.com/og-docs.png
---

[Skip to content](#main-content)

> Documentation Index  
> Fetch the complete documentation index at: https://developers.cloudflare.com/d1/llms.txt  
> Use this file to discover all available pages before exploring further.

# Return objects

Last updated Apr 21, 2026|Copy as Markdown| [View as Markdown](https://developers.cloudflare.com/d1/worker-api/return-object/index.md)| [Agent setup](https://developers.cloudflare.com/agent-setup/)

Some D1 Worker Binding APIs return a typed object.

| D1 Worker Binding API | Return object |
| --- | --- |
| [`D1PreparedStatement::run`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#run), [`D1Database::batch`](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch) | `D1Result` |
| [`D1Database::exec`](https://developers.cloudflare.com/d1/worker-api/d1-database/#exec) | `D1ExecResult` |

## `D1Result`

The methods [`D1PreparedStatement::run`](https://developers.cloudflare.com/d1/worker-api/prepared-statements/#run) and [`D1Database::batch`](https://developers.cloudflare.com/d1/worker-api/d1-database/#batch) return a typed [`D1Result`](#d1result) object for each query statement. This object contains:

- The success status
- A meta object with the internal duration of the operation in milliseconds
- The results (if applicable) as an array

```js
{
  success: boolean, // true if the operation was successful, false otherwise
  meta: {
    served_by: string // the version of Cloudflare's backend Worker that returned the result
    served_by_region: string // the region of the database instance that executed the query
    served_by_primary: boolean // true if (and only if) the database instance that executed the query was the primary
    timings: {
      sql_duration_ms: number // the duration of the SQL query execution by the database instance (not including any network time)
    }
    duration: number, // the duration of the SQL query execution only, in milliseconds
		changes: number, // the number of changes made to the database
		last_row_id: number, // the last inserted row ID, only applies when the table is defined without the `WITHOUT ROWID` option
		changed_db: boolean, // true if something on the database was changed
    size_after: number, // the size of the database after the query is successfully applied
    rows_read: number, // the number of rows read (scanned) by this query
    rows_written: number // the number of rows written by this query
    total_attempts: number //the number of total attempts to successfully execute the query, including retries
  }
  results: array | null, // [] if empty, or null if it does not apply
}
```

### Example

```js
const someVariable = `Bs Beverages`;
const stmt = env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(someVariable);
const returnValue = await stmt.run();
return Response.json(returnValue)
```

```py
from workers import Response

some_variable = "Bs Beverages"
stmt = self.env.DB.prepare("SELECT * FROM Customers WHERE CompanyName = ?").bind(some_variable)
return_value = await stmt.run()
return Response.json(return_value)
```

```json
{
  "success": true,
  "meta": {
    "served_by": "miniflare.db",
    "served_by_region": "WEUR",
    "served_by_primary": true,
    "timings": {
      "sql_duration_ms": 0.2552
    },
    "duration": 0.2552,
    "changes": 0,
    "last_row_id": 0,
    "changed_db": false,
    "size_after": 16384,
    "rows_read": 4,
    "rows_written": 0
  },
  "results": [
    {
      "CustomerId": 11,
      "CompanyName": "Bs Beverages",
      "ContactName": "Victoria Ashworth"
    },
    {
      "CustomerId": 13,
      "CompanyName": "Bs Beverages",
      "ContactName": "Random Name"
    }
  ]
}
```

## `D1ExecResult`

The method [`D1Database::exec`](https://developers.cloudflare.com/d1/worker-api/d1-database/#exec) returns a typed [`D1ExecResult`](#d1execresult) object for each query statement. This object contains:

- The number of executed queries
- The duration of the operation in milliseconds

```js
{
	"count": number, // the number of executed queries
	"duration": number // the duration of the operation, in milliseconds
}
```

### Example

```js
const returnValue = await env.DB.exec(`SELECT * FROM Customers WHERE CompanyName = "Bs Beverages"`);
return Response.json(returnValue);
```

```py
from workers import Response

return_value = await self.env.DB.exec('SELECT * FROM Customers WHERE CompanyName = "Bs Beverages"')
return Response.json(return_value)
```

```json
{
  "count": 1,
  "duration": 1
}
```

Storing large numbers

Any numeric value in a column is affected by JavaScript's 52-bit precision for numbers. If you store a very large number (in `int64`), then retrieve the same value, the returned value may be less precise than your original number.

Was this helpful?

YesNo

## On this page

[![](https://developers.cloudflare.com/_astro/logo.te5VL_aD.svg)Docs](https://developers.cloudflare.com/)

```json
{"@context":"https://schema.org","@type":"TechArticle","@id":"https://developers.cloudflare.com/d1/worker-api/return-object/#page","headline":"Return objects","description":"Understand the D1Result and D1ExecResult objects returned by D1 Worker Binding API query methods.","url":"https://developers.cloudflare.com/d1/worker-api/return-object/","inLanguage":"en","image":"https://developers.cloudflare.com/og-docs.png","dateModified":"2026-04-21","publisher":{"@type":"Organization","name":"Cloudflare","description":"One platform for your apps, agents, and workforce. Build, secure, and scale without managing infrastructure","url":"https://www.cloudflare.com/","sameAs":["https://github.com/cloudflare","https://www.linkedin.com/company/cloudflare","https://x.com/cloudflare"],"logo":{"@type":"ImageObject","url":"https://developers.cloudflare.com/logo.svg"},"address":{"@type":"PostalAddress","streetAddress":"101 Townsend St","addressLocality":"San Francisco","addressRegion":"CA","postalCode":"94107","addressCountry":"US"},"contactPoint":[{"@type":"ContactPoint","contactType":"Customer Support","url":"https://support.cloudflare.com/","availableLanguage":["English"]},{"@type":"ContactPoint","contactType":"Sales","url":"https://www.cloudflare.com/contact/","availableLanguage":["English"]}]},"isPartOf":{"@type":"WebSite","@id":"https://developers.cloudflare.com/#website","name":"Cloudflare Docs","url":"https://developers.cloudflare.com/"}}
```

```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.5s)

_Thinking:_



_Thinking:_



**Tool: websearch**

**Input:**
```json
{
  "query": "Cloudflare Python Workers JsProxy to_py dict conversion FFI documentation",
  "type": "deep"
}
```

**Output:**
```
{
  "search_id": "search_ec7c1822ae30287ff67ab9b51ddd04d2",
  "results": [
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/ffi",
      "title": "Foreign Function Interface (FFI) - Cloudflare Docs",
      "publish_date": null,
      "excerpts": [
        "description: Call JavaScript APIs, bindings, and globals from Python Workers using the Pyodide FFI. title: Foreign Function Interface (FFI) image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/workers/llms.txt Use this file to discover all available pages before exploring further.\nForeign Function Interface (FFI)\nLast updated Jun 22, 2026|Copy as Markdown|View as Markdown|Agent setup\nVia Pyodide ↗, Python Workers provide a Foreign Function Interface (FFI) ↗ to JavaScript. This allows you to:\n* Use bindings to resources on Cloudflare, including Workers AI, Vectorize, R2, KV, D1, Queues, Durable Objects, Service Bindings and more.\n* Use JavaScript globals, like Request, Response, and fetch().\n* Use the full feature set of Cloudflare Workers — if an API is accessible in JavaScript, you can also access it in a Python Worker, writing exclusively Python code.\nThe details of Pyodide's Foreign Function Interface are documented here ↗, and Workers written in Python are able to take full advantage of this.\nUsing Bindings from Python Workers\nBindings allow your Worker to interact with resources on the Cloudflare Developer Platform. When you declare a binding on your Worker, you grant it a specific capability, such as being able to read and write files to an R2 bucket.\nFor example, to access a KV namespace from a Python Worker, you would declare the following in your Worker's Wrangler configuration file:\n{\n\"main\": \"./src/index.py\",\n\"kv_namespaces\": [\n{\n\"binding\": \"FOO\",\n\"id\": \"<YOUR_KV_NAMESPACE_ID>\"\n}\n]\n}\nmain = \"./src/index.py\"\n[[kv_namespaces]]\nbinding = \"FOO\"\nid = \"<YOUR_KV_NAMESPACE_ID>\"\n...and then call .get() on the binding object that is exposed on env:\nfrom workers import WorkerEntrypoint, Response\nclass Default(WorkerEntrypoint):\nasync def fetch(self, request):\nawait self.env.FOO.put(\"bar\", \"baz\")\nbar = await self.env.FOO.get(\"bar\")\nreturn Response(bar) # returns \"baz\"\nConverting Python to JavaScript\nOccasionally, to interoperate with JavaScript APIs, you may need to convert a Python object to JavaScript. Pyodide provides a to_js function to facilitate this conversion.\nfrom js import Object\nfrom pyodide.ffi import to_js as _to_js\nfrom workers import WorkerEntrypoint, Response\nto_js converts between Python dictionaries and JavaScript Objects\ndef to_js(obj):\nreturn _to_js(obj, dict_converter=Object.fromEntries)\nFor more details, see out the documentation on pyodide.ffi.to_js ↗.\nUsing JavaScript globals from Python Workers\nto_js converts between Python dictionaries and JavaScript Objects\nFFI.\",\"url\":\"https://developers.cloudflare.com/workers/languages/python/ffi/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-06-22\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"url\":\"https://www.cloudflare.com/\"},\"i"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/",
      "title": "Write Cloudflare Workers in Python · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "When you initialize a new Python Worker project and select from one of many templates: uv run pywrangler init Or you can clone the examples repository to explore more options: git clone https://github.com/cloudflare/python-workers-examples cd python-workers-examples/hello\nNext Up\nLearn more about the basics of Python Workers\nLearn details about local development, deployment, and how to Python Workers work.\nExplore the package docs for instructions on how to use packages with Python Workers.\nUnderstand which parts of the Python Standard Library are supported in Python Workers.\nLearn about Python Workers' foreign function interface (FFI), and how to use it to work with bindings and Runtime APIs. Was this helpful? YesNo\nOn this page"
      ]
    },
    {
      "url": "https://developers.cloudflare.com/workers/languages/python/examples",
      "title": "Python Worker Examples · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "description: Python code examples demonstrating modules, bindings, and SDK usage in Workers. title: Examples image: https://developers.cloudflare.com/og-docs.png\nSkip to content\nDocumentation Index Fetch the complete documentation index at: https://developers.cloudflare.com/workers/llms.txt Use this file to discover all available pages before exploring further.\nExamples\nLast updated Jul 6, 2026|Copy as Markdown|View as Markdown|Agent setup\nCloudflare has a wide range of Python examples in the Workers Example gallery.\nIn addition to those examples, consider the following ones that illustrate Python-specific behavior.\nModules in your Worker\nParse an incoming request URL\nfrom workers import WorkerEntrypoint, Response\nfrom urllib.parse import urlparse, parse_qs\nclass Default(WorkerEntrypoint):\nasync def fetch(self, request):\n# Parse the incoming request URL\nurl = urlparse(request.url)\n# Parse the query parameters into a Python dictionary\nparams = parse_qs(url.query)\n```\n    if \"name\" in params:\n        greeting = \"Hello there, {name}\".format(name=params[\"name\"][0])\n        return Response(greeting)\n\n\n    if url.path == \"/favicon.ico\":\n      return Response(\"\")\n\n    return Response(\"Hello world!\")\n```\nParse JSON from the incoming request\nfrom workers import WorkerEntrypoint, Response\nclass Default(WorkerEntrypoint):\nasync def fetch(self, request):\nbody = await request.json()  # returns a native Python dict\nname = body[\"name\"]\nreturn Response(\"Hello, {name}\".format(name=name))\nReturn a JSON response\nfrom workers import WorkerEntrypoint, Response\nTo use the native Python logging\nRefer to Durable Objects documentation for more information.\nCron Trigger\nfrom workers import WorkerEntrypoint\nTo use the native Python logging\nRefer to the Python Workflows documentation for more information.\nMore Examples\nOr you can clone the examples repository ↗ to explore even more examples:\ngit clone https://github.com/cloudflare/python-workers-examples\nWas this helpful?\nYesNo\nOn this page\nTo use the native Python logging\nDocs\n{\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/workers/languages/python/examples/#page\",\"headline\":\"Python Worker Examples · Cloudflare Workers docs\",\"description\":\"Python code examples demonstrating modules, bindings, and SDK usage in\nTo use the native Python logging\nWorkers.\",\"url\":\"https://developers.cloudflare.com/workers/languages/python/examples/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-07-06\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"url\":\"https://www.cloudflare.com/\"},\"isPartOf\":{\"@type\":\"WebSi"
      ]
    },
    {
      "url": "https://pyodide.org/en/0.27.0/usage/api/python-api/ffi.html",
      "title": "pyodide.ffi — Version 0.27.0",
      "publish_date": null,
      "excerpts": [
        "An error thrown when conversion between JavaScript and Python fails.\nclass pyodide.ffi.JsArray#\nBases: JsIterable[T], Generic[T], MutableSequence[T]\nA JsProxy of an Array, NodeList, or TypedArray\nappend(object)#\nAppend object to the end of the list.\nParameters:\nobject (T)\nReturn type:\nNone\ncount(x)#\nReturn the number of times x appears in the list.\nReverse the array in place.\nReturn type:\nNone\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\n* depth (int) – Limit the depth of the conversion. If a shallow conversion is desired, set depth to 1.\n* onrejected (Callable[[BaseException], Union[Awaitable[S], S]] | None)\nReturn type:\nJsPromise[S]\nclass pyodide.ffi.JsProxy#\nBases: object\nA proxy to make a JavaScript object behave like a Python object\nFor more information see the Type translations documentation.\nReturns a new JsProxy that treats a JavaScript object as Python json.\nIt allows one to treat a JavaScript object that is a mixture of JavaScript arrays and objects as a mixture of Python lists and dicts.\nThis method is not present on typed arrays, array buffers, functions, and errors.\nReturn type:\nUnion[JsMutableMap[str, Any], JsArray[Any]]\nif isinstance(obj, JsProxy): ... if obj.constructor.name == \"Array\": ... return list(obj) ... return dict(obj)\nFor example:\nimport json json.dumps(o1.as_py_json(), default=default) '{\"x\": {\"y\": 2}}' json.dumps(o2.as_py_json(), default=default) '[{\"x\": 2}, {\"x\": 7}]'\nIf you load the resulting json back into Python, the result is the same as calling JsProxy.to_py():\nassert json.loads(json.dumps(o1.as_py_json(), default=default)) == o1.to_py() assert json.loads(json.dumps(o2.as_py_json(), default=default)) == o2.to_py()\nbind_sig(signature)#\nCreates a copy of the JsProxy with a signature bound to it.\nExperimental\nfrom pyodide.code import run_js js_obj = run_js(\"({first: 1, second: 2, third: 3})\") values = js_obj.object_values() list(values) [1, 2, 3]\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\nIt is expected to return the desired result of the dict conversion. Some suggested values for this argument:\n* js.Map.new – similar to the default behavior\n* js.Array.from – convert to an array of entries\n* js.Object.fromEntries – convert to a JavaScript object"
      ]
    },
    {
      "url": "https://pyodide.org/en/0.28.2/usage/api/python-api/ffi.html",
      "title": "pyodide.ffi",
      "publish_date": null,
      "excerpts": [
        "js_obj.object_values() list(values) [1, 2, 3] to_py(*, depth=-1, default_converter=None)# Convert the JsProxy to a native Python object as best as possible. See JavaScript to Python for more information. Parameters:\ndepth (int) – Limit the depth of the conversion. If a shallow conversion is desired, set depth to 1.\ndefault_converter (Callable[[JsProxy, Callable[[JsProxy], Any], Callable[[JsProxy, Any], None]], Any] | None) – If present, this will be invoked whenever Pyodide does not have some built in conversion for the object. If default_converter raises an error, the error will be allowed to propagate. Otherwise, the object returned will be used as the conversion. default_converter takes three arguments. The first argument is the value to be converted. Skip to main content Back to"
      ]
    },
    {
      "url": "https://9a798b9b.previews.developers.cloudflare.com/workers/languages/python/ffi/index.md",
      "title": "Foreign Function Interface (FFI)",
      "publish_date": null,
      "excerpts": [
        "Docs {\"@context\":\"https://schema.org\",\"@type\":\"TechArticle\",\"@id\":\"https://developers.cloudflare.com/workers/languages/python/ffi/#page\",\"headline\":\"Work with JavaScript objects, methods, functions and globals from Python Workers · Cloudflare Workers docs\",\"description\":\"Call JavaScript APIs, bindings, and globals from Python Workers using the Pyodide FFI.\",\"url\":\"https://developers.cloudflare.com/workers/languages/python/ffi/\",\"inLanguage\":\"en\",\"image\":\"https://developers.cloudflare.com/og-docs.png\",\"dateModified\":\"2026-08-27\",\"publisher\":{\"@type\":\"Organization\",\"name\":\"Cloudflare\",\"description\":\"One platform for your apps, agents, and workforce."
      ]
    },
    {
      "url": "https://5b04bc4a.preview.developers.cloudflare.com/workers/languages/python/ffi/",
      "title": "Work with JavaScript objects, methods, functions and globals from Python Workers · Cloudflare Workers docs",
      "publish_date": null,
      "excerpts": [
        "Use bindings to resources on Cloudflare, including Workers AI, Vectorize, R2, KV, D1, Queues, Durable Objects, Service Bindings and more.\nUse JavaScript globals, like Request, Response, and fetch().\nUse the full feature set of Cloudflare Workers — if an API is accessible in JavaScript, you can also access it in a Python Worker, writing exclusively Python code. The details of Pyodide's Foreign Function Interface are documented here ↗, and Workers written in Python are able to take full advantage of this.\nUsing Bindings from Python Workers"
      ]
    },
    {
      "url": "https://pyodide.org/en/0.29.2/usage/api/python-api/ffi.html",
      "title": "pyodide.ffi — Version 0.29.2",
      "publish_date": null,
      "excerpts": [
        "* ConversionError | An error thrown when conversion between JavaScript and Python fails.\n* JsException(*args, **kwargs) | A JavaScript Error.\nClasses:\n* JsArray() | A JsProxy of an Array, NodeList, or TypedArray\n* JsAsyncGenerator() | A JavaScript AsyncGenerator\n* JsAsyncIterable() | A JavaScript async iterable object\n* JsNull() | The type of the Python representation of the JavaScript null object\n* JsOnceCallable() | A JavaScript handle for a Python function which can be called at most once.\n* JsPromise() | A JsProxy of a Promise or some other thenable JavaScript object.\n* JsProxy() | A proxy to make a JavaScript object behave like a Python object\n* to_js(obj, /, *[, depth, pyproxies, ...]) | Convert the object to JavaScript.\n* unregister_js_module(name) | Unregisters a JavaScript module with given name that has been previously registered with pyodide.registerJsModule() or pyodide.ffi.register_js_module().\nData:\n* jsnull | The Python representation of the JavaScript null object.\nexception pyodide.ffi.ConversionError#\nBases: Exception\nAn error thrown when conversion between JavaScript and Python fails.\nclass pyodide.ffi.JsArray#\nBases: JsIterable[T], Generic[T], MutableSequence[T]\nA JsProxy of an Array, NodeList, or TypedArray\nappend(object)#\nAppend object to the end of the list.\nParameters:\nobject (T)\nReturn type:\nNone\nParameters:\nvalue (T)\nReturn type:\nNone\nreverse()#\nReverse the array in place.\nReturn type:\nNone\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\n* depth (int) – Limit the depth of the conversion.\nclass pyodide.ffi.JsProxy#\nBases: object\nA proxy to make a JavaScript object behave like a Python object\nFor more information see the Type translations documentation. In particular, see the list of __dunder__ methodsthat are (conditionally) implemented on JsProxy.\nas_object_map(*, hereditary=False)#\nIf you load the resulting json back into Python, the result is the same as calling JsProxy.to_py():\nassert json.loads(json.dumps(o1.as_py_json(), default=default)) == o1.to_py() assert json.loads(json.dumps(o2.as_py_json(), default=default)) == o2.to_py()\nbind_class(signature)#\nCreates a copy of the JsProxy with a signature bound to it.\nfrom pyodide.code import run_js js_obj = run_js(\"({first: 1, second: 2, third: 3})\") values = js_obj.object_values() list(values) [1, 2, 3]\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\nThis method is necessary because indexing the Array from Python automatically unwraps the PyProxy into the wrapped Python object.\nParameters:\npyproxies (JsArray[Any])\nReturn type:\nNone\npyodide.ffi.jsnull_: JsNull_ = jsnull#\nThe Python representation of the JavaScript null object.\npyodide.ffi.register_js_module(name, jsproxy)#"
      ]
    },
    {
      "url": "https://pyodide.org/en/0.27.6/usage/api/python-api/ffi.html",
      "title": "pyodide.ffi",
      "publish_date": null,
      "excerpts": [
        "* ConversionError | An error thrown when conversion between JavaScript and Python fails.\n* JsException(*args, **kwargs) | A JavaScript Error.\nClasses:\n* JsArray() | A JsProxy of an Array, NodeList, or TypedArray\n* JsAsyncGenerator() | A JavaScript AsyncGenerator\n* JsAsyncIterable() | A JavaScript async iterable object\n* JsPromise() | A JsProxy of a Promise or some other thenable JavaScript object.\n* JsProxy() | A proxy to make a JavaScript object behave like a Python object\n* JsTypedArray() |\n* ToJsConverter(*args, **kwargs) | Protocol for the default_converter and eager_converter arguments of to_js().\nFunctions:\n* unregister_js_module(name) | Unregisters a JavaScript module with given name that has been previously registered with pyodide.registerJsModule() or pyodide.ffi.register_js_module().\nexception pyodide.ffi.ConversionError#\nBases: Exception\nAn error thrown when conversion between JavaScript and Python fails.\nclass pyodide.ffi.JsArray#\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\n* depth (int) – Limit the depth of the conversion. If a shallow conversion is desired, set depth to 1.\n* onrejected (Callable[[BaseException], Union[Awaitable[S], S]] | None)\nReturn type:\nJsPromise[S]\nclass pyodide.ffi.JsProxy#\nBases: object\nA proxy to make a JavaScript object behave like a Python object\nFor more information see the Type translations documentation.\nReturns a new JsProxy that treats a JavaScript object as Python json.\nIt allows one to treat a JavaScript object that is a mixture of JavaScript arrays and objects as a mixture of Python lists and dicts.\nThis method is not present on typed arrays, array buffers, functions, and errors.\nReturn type:\nUnion[JsMutableMap[str, Any], JsArray[Any]]\nIf you load the resulting json back into Python, the result is the same as calling JsProxy.to_py():\nassert json.loads(json.dumps(o1.as_py_json(), default=default)) == o1.to_py() assert json.loads(json.dumps(o2.as_py_json(), default=default)) == o2.to_py()\nbind_class(signature)#\nCreates a copy of the JsProxy with a signature bound to it.\nfrom pyodide.code import run_js js_obj = run_js(\"({first: 1, second: 2, third: 3})\") values = js_obj.object_values() list(values) [1, 2, 3]\nto_py(*, depth=-1, default_converter=None)#\nConvert the JsProxy to a native Python object as best as possible.\nSee JavaScript to Python for more information.\nParameters:\n* dict_converter (Callable[[Iterable[JsArray[Any]]], JsProxy] | None) – This converter if provided receives a (JavaScript) iterable of (JavaScript) pairs [key, value]. It is expected to return the desired result of the dict conversion. Some suggested values for this argument:\n* js.Map.new – similar to the default behavior"
      ]
    },
    {
      "url": "https://blog.cloudflare.com/python-workers-ga",
      "title": "Python Workers are now generally available",
      "publish_date": null,
      "excerpts": [
        "Python Workers are now generally available\nPython Workers allow developers to run Python web frameworks and AI orchestration libraries natively in the Cloudflare Workers runtime."
      ]
    }
  ],
  "warnings": null,
  "metadata": null,
  "session_id": "ses_f1bfef7dbffeJFSNLNDT39shaW"
}
```

---

## Assistant (Build · Muse Spark 1.3 Free · 8.4s)

_Thinking:_

Comparing D1 binding methods and confirming run and all return similar results.

**Tool: webfetch**

**Input:**
```json
{
  "format": "text",
  "url": "https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/fastapi-todo/src/app.py"
}
```

**Error:**
```
StatusCode: non 2xx status code (404 GET https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/fastapi-todo/src/app.py)
```

**Tool: webfetch**

**Input:**
```json
{
  "format": "text",
  "url": "https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/query-d1/src/entry.py"
}
```

**Output:**
```
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        query = """
        SELECT quote, author
        FROM qtable
        ORDER BY RANDOM()
        LIMIT 1;
        """
        results = await self.env.DB.prepare(query).all()
        data = results.results[0]

        # Return a JSON response
        return Response.json(data)

```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.5s)

_Thinking:_



**Tool: webfetch**

**Input:**
```json
{
  "format": "markdown",
  "url": "https://github.com/cloudflare/python-workers-examples/tree/main/fastapi-todo"
}
```

**Output:**
```
                                                                                                               python-workers-examples/fastapi-todo at main · cloudflare/python-workers-examples · GitHub                                             

[Skip to content](#start-of-content)     

    

            

## Navigation Menu

[](/)

[Sign in](/login?return_to=https%3A%2F%2Fgithub.com%2Fcloudflare%2Fpython-workers-examples%2Ftree%2Fmain%2Ffastapi-todo)

Appearance settings

-   Platform
    
    -   AI CODE CREATION
        
        -   [GitHub CopilotWrite better code with AI](https://github.com/features/copilot)
        -   [GitHub Copilot appDirect agents from issue to merge](https://github.com/features/ai/github-app)
        -   [MCP RegistryIntegrate external tools](https://github.com/mcp)
        
    -   DEVELOPER WORKFLOWS
        
        -   [ActionsAutomate any workflow](https://github.com/features/actions)
        -   [CodespacesInstant dev environments](https://github.com/features/codespaces)
        -   [IssuesPlan and track work](https://github.com/features/issues)
        -   [Code ReviewManage code changes](https://github.com/features/code-review)
        -   [Code QualityEnforce quality at merge](https://github.com/features/code-quality)
        
    -   APPLICATION SECURITY
        
        -   [GitHub Advanced SecurityFind and fix vulnerabilities](https://github.com/security/advanced-security)
        -   [Code securitySecure your code as you build](https://github.com/security/advanced-security/code-security)
        -   [Secret protectionStop leaks before they start](https://github.com/security/advanced-security/secret-protection)
        
    -   EXPLORE
        
        -   [Why GitHub](https://github.com/why-github)
        -   [Documentation](https://docs.github.com)
        -   [Blog](https://github.blog)
        -   [Changelog](https://github.blog/changelog)
        -   [Marketplace](https://github.com/marketplace)
        
    
    [View all features](https://github.com/features)
    
-   Solutions
    
    -   BY COMPANY SIZE
        
        -   [Enterprises](https://github.com/enterprise)
        -   [Small and medium teams](https://github.com/team)
        -   [Startups](https://github.com/enterprise/startups)
        -   [Nonprofits](https://github.com/solutions/industry/nonprofits)
        
    -   BY USE CASE
        
        -   [App Modernization](https://github.com/solutions/use-case/app-modernization)
        -   [DevSecOps](https://github.com/solutions/use-case/devsecops)
        -   [DevOps](https://github.com/solutions/use-case/devops)
        -   [CI/CD](https://github.com/solutions/use-case/ci-cd)
        -   [View all use cases](https://github.com/solutions/use-case)
        
    -   BY INDUSTRY
        
        -   [Healthcare](https://github.com/solutions/industry/healthcare)
        -   [Financial services](https://github.com/solutions/industry/financial-services)
        -   [Manufacturing](https://github.com/solutions/industry/manufacturing)
        -   [Government](https://github.com/solutions/industry/government)
        -   [View all industries](https://github.com/solutions/industry)
        
    
    [View all solutions](https://github.com/solutions)
    
-   Resources
    
    -   EXPLORE BY TOPIC
        
        -   [AI](https://github.com/resources/articles?topic=ai)
        -   [Software Development](https://github.com/resources/articles?topic=software-development)
        -   [DevOps](https://github.com/resources/articles?topic=devops)
        -   [Security](https://github.com/resources/articles?topic=security)
        -   [View all topics](https://github.com/resources/articles)
        
    -   EXPLORE BY TYPE
        
        -   [Customer stories](https://github.com/customer-stories)
        -   [Events & webinars](https://github.com/resources/events)
        -   [Ebooks & reports](https://github.com/resources/whitepapers)
        -   [Business insights](https://github.com/solutions/executive-insights)
        -   [GitHub Skills](https://skills.github.com)
        
    -   SUPPORT & SERVICES
        
        -   [Documentation](https://docs.github.com)
        -   [Customer support](https://support.github.com)
        -   [Community forum](https://github.com/orgs/community/discussions)
        -   [Trust center](https://github.com/trust-center)
        -   [Partners](https://github.com/partners)
        
    
    [View all resources](https://github.com/resources)
    
-   Open Source
    
    -   COMMUNITY
        
        -   [GitHub SponsorsFund open source developers](https://github.com/open-source/sponsors)
        
    -   PROGRAMS
        
        -   [Security Lab](https://securitylab.github.com)
        -   [Maintainer Community](https://maintainers.github.com)
        -   [GitHub Stars](https://stars.github.com)
        -   [Archive Program](https://archiveprogram.github.com)
        
    -   REPOSITORIES
        
        -   [Topics](https://github.com/topics)
        -   [Trending](https://github.com/trending)
        -   [Collections](https://github.com/collections)
        
    
-   Enterprise
    
    -   ENTERPRISE SOLUTIONS
        
        -   [Enterprise platformAI-powered developer platform](https://github.com/enterprise)
        
    -   AVAILABLE ADD-ONS
        
        -   [GitHub Advanced SecurityEnterprise-grade security features](https://github.com/security/advanced-security)
        -   [Copilot for BusinessEnterprise-grade AI features](https://github.com/features/copilot/copilot-business)
        -   [Premium SupportEnterprise-grade 24/7 support](https://github.com/enterprise/premium-support)
        
    
-   [Pricing](https://github.com/pricing)

Search/

[Sign in](/login?return_to=https%3A%2F%2Fgithub.com%2Fcloudflare%2Fpython-workers-examples%2Ftree%2Fmain%2Ffastapi-todo)

[Sign up](/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F%3Cuser-name%3E%2F%3Crepo-name%3E%2Ffiles%2Fdisambiguate&source=header-repo&source_repo=cloudflare%2Fpython-workers-examples)

Appearance settings

You signed in with another tab or window. Reload to refresh your session. You signed out in another tab or window. Reload to refresh your session. You switched accounts on another tab or window. Reload to refresh your session. Dismiss alert

[cloudflare](/cloudflare) / **[python-workers-examples](/cloudflare/python-workers-examples)** Public

-   [Notifications](/login?return_to=%2Fcloudflare%2Fpython-workers-examples) You must be signed in to change notification settings
-   [Fork 72](/login?return_to=%2Fcloudflare%2Fpython-workers-examples)
-   [Star 334](/login?return_to=%2Fcloudflare%2Fpython-workers-examples)
    

-   [Code](/cloudflare/python-workers-examples)
-   [Issues 10](/cloudflare/python-workers-examples/issues)
-   [Pull requests 14](/cloudflare/python-workers-examples/pulls)
-   [Actions](/cloudflare/python-workers-examples/actions)
-   [Projects](/cloudflare/python-workers-examples/projects)
-   [Security and quality 0](/cloudflare/python-workers-examples/security)
-   [Insights](/cloudflare/python-workers-examples/pulse)

Additional navigation options

-   [Code](/cloudflare/python-workers-examples)
-   [Issues](/cloudflare/python-workers-examples/issues)
-   [Pull requests](/cloudflare/python-workers-examples/pulls)
-   [Actions](/cloudflare/python-workers-examples/actions)
-   [Projects](/cloudflare/python-workers-examples/projects)
-   [Security and quality](/cloudflare/python-workers-examples/security)
-   [Insights](/cloudflare/python-workers-examples/pulse)

 [](/cloudflare/python-workers-examples)

## FilesExpand file tree

main

## Breadcrumbs

1.  [python-workers-examples](/cloudflare/python-workers-examples/tree/main)

/

# fastapi-todo

/

Copy path

## Directory actions

## More options

More options

## Directory actions

## More options

More options

## Latest commit

## History

[History](/cloudflare/python-workers-examples/commits/main/fastapi-todo)

[](/cloudflare/python-workers-examples/commits/main/fastapi-todo)History

main

## Breadcrumbs

1.  [python-workers-examples](/cloudflare/python-workers-examples/tree/main)

/

# fastapi-todo

/

Copy path

Top

## Folders and files

Name

Name

Last commit message

Last commit date

### parent directory

[

..

](/cloudflare/python-workers-examples/tree/main)

[src](/cloudflare/python-workers-examples/tree/main/fastapi-todo/src "src")

[src](/cloudflare/python-workers-examples/tree/main/fastapi-todo/src "src")

[README.md](/cloudflare/python-workers-examples/blob/main/fastapi-todo/README.md "README.md")

[README.md](/cloudflare/python-workers-examples/blob/main/fastapi-todo/README.md "README.md")

[db\_init.sql](/cloudflare/python-workers-examples/blob/main/fastapi-todo/db_init.sql "db_init.sql")

[db\_init.sql](/cloudflare/python-workers-examples/blob/main/fastapi-todo/db_init.sql "db_init.sql")

[package.json](/cloudflare/python-workers-examples/blob/main/fastapi-todo/package.json "package.json")

[package.json](/cloudflare/python-workers-examples/blob/main/fastapi-todo/package.json "package.json")

[pyproject.toml](/cloudflare/python-workers-examples/blob/main/fastapi-todo/pyproject.toml "pyproject.toml")

[pyproject.toml](/cloudflare/python-workers-examples/blob/main/fastapi-todo/pyproject.toml "pyproject.toml")

[wrangler.jsonc](/cloudflare/python-workers-examples/blob/main/fastapi-todo/wrangler.jsonc "wrangler.jsonc")

[wrangler.jsonc](/cloudflare/python-workers-examples/blob/main/fastapi-todo/wrangler.jsonc "wrangler.jsonc")

View all files

## [README.md](#readme)

Outline

# FastAPI Todo Backend

[](#fastapi-todo-backend)

A Python FastAPI implementation of the [Todo-Backend](https://todobackend.com) spec, running on Cloudflare Workers with D1 for storage.

## Development

[](#development)

Initialize the local D1 database and start the dev server:

uv run pywrangler d1 execute todos --local --file db\_init.sql
uv run pywrangler dev

## Testing with the Todo-Backend spec runner

[](#testing-with-the-todo-backend-spec-runner)

Start the dev server, then open the spec runner pointing at your local instance:

```
https://todobackend.com/specs/index.html?http://localhost:8787/todos
```

You can also use the Todo-Backend client app:

```
https://todobackend.com/client/index.html?http://localhost:8787/todos
```

## API

[](#api)

Method

Path

Description

`GET`

`/todos`

List all todos

`POST`

`/todos`

Create a todo

`DELETE`

`/todos`

Delete all todos

`GET`

`/todos/{id}`

Get a single todo

`PATCH`

`/todos/{id}`

Update a todo

`DELETE`

`/todos/{id}`

Delete a todo

## Footer

[](https://github.com)© 2026 GitHub, Inc.

### Footer navigation

-   [Terms](https://docs.github.com/site-policy/github-terms/github-terms-of-service)
-   [Privacy](https://docs.github.com/site-policy/privacy-policies/github-privacy-statement)
-   [Security](https://github.com/security)
-   [Status](https://www.githubstatus.com/)
-   [Community](https://github.community/)
-   [Docs](https://docs.github.com/)
-   [Contact](https://support.github.com?tags=dotcom-footer)
-   Manage cookies
-   Do not share my personal information

You can’t perform that action at this time.
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.3s)

_Thinking:_



**Tool: bash**

**Input:**
```json
{
  "command": "python3 -c \"import urllib.request, json; print(urllib.request.urlopen('https://api.github.com/repos/cloudflare/python-workers-examples/contents/fastapi-todo/src').read().decode())\""
}
```

**Output:**
```
[{"name":"worker.py","path":"fastapi-todo/src/worker.py","sha":"e5e1fc577d0eeaa5321df63757994e8efa48f7f8","size":3292,"url":"https://api.github.com/repos/cloudflare/python-workers-examples/contents/fastapi-todo/src/worker.py?ref=main","html_url":"https://github.com/cloudflare/python-workers-examples/blob/main/fastapi-todo/src/worker.py","git_url":"https://api.github.com/repos/cloudflare/python-workers-examples/git/blobs/e5e1fc577d0eeaa5321df63757994e8efa48f7f8","download_url":"https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/fastapi-todo/src/worker.py","type":"file","_links":{"self":"https://api.github.com/repos/cloudflare/python-workers-examples/contents/fastapi-todo/src/worker.py?ref=main","git":"https://api.github.com/repos/cloudflare/python-workers-examples/git/blobs/e5e1fc577d0eeaa5321df63757994e8efa48f7f8","html":"https://github.com/cloudflare/python-workers-examples/blob/main/fastapi-todo/src/worker.py"}}]

```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.5s)

**Tool: webfetch**

**Input:**
```json
{
  "format": "text",
  "url": "https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/fastapi-todo/src/worker.py"
}
```

**Output:**
```
import uuid

from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Request

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _base_url(request: Request) -> str:
    """Return the root URL for the todos collection."""
    return str(request.base_url).rstrip("/") + "/todos"


def _row_to_todo(row, request: Request) -> dict:
    """Convert a D1 row into a todo dict with the absolute ``url`` field."""
    return {
        "id": row.id,
        "title": row.title,
        "completed": bool(row.completed),
        "order": row.order,
        "url": f"{_base_url(request)}/{row.id}",
    }


def _db(request: Request):
    """Get the D1 database binding from the ASGI scope."""
    return request.scope["env"].DB


@app.get("/todos")
async def list_todos(request: Request):
    results = await _db(request).prepare("SELECT * FROM todos").all()
    return [_row_to_todo(r, request) for r in results.results]


@app.post("/todos")
async def create_todo(request: Request):
    body = await request.json()
    todo_id = str(uuid.uuid4())
    title = body.get("title", "")
    completed = 1 if body.get("completed", False) else 0
    order = body.get("order")

    await (
        _db(request)
        .prepare(
            'INSERT INTO todos (id, title, completed, "order") VALUES (?, ?, ?, ?)'
        )
        .bind(todo_id, title, completed, order)
        .run()
    )

    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )

    return _row_to_todo(row, request)


@app.delete("/todos")
async def delete_all_todos(request: Request):
    await _db(request).prepare("DELETE FROM todos").run()
    return []


@app.get("/todos/{todo_id}")
async def get_todo(todo_id: str, request: Request):
    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )
    if row is None:
        return {"error": "not found"}
    return _row_to_todo(row, request)


@app.patch("/todos/{todo_id}")
async def update_todo(todo_id: str, request: Request):
    body = await request.json()
    sets = []
    values = []
    if "title" in body:
        sets.append("title = ?")
        values.append(body["title"])
    if "completed" in body:
        sets.append("completed = ?")
        values.append(1 if body["completed"] else 0)
    if "order" in body:
        sets.append('"order" = ?')
        values.append(body["order"])

    if sets:
        values.append(todo_id)
        await (
            _db(request)
            .prepare(f"UPDATE todos SET {', '.join(sets)} WHERE id = ?")
            .bind(*values)
            .run()
        )

    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )
    if row is None:
        return {"error": "not found"}
    return _row_to_todo(row, request)


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str, request: Request):
    await _db(request).prepare("DELETE FROM todos WHERE id = ?").bind(todo_id).run()
    return []


import asgi

Default = asgi.entrypoint(app)

```

---

## Assistant (Build · Muse Spark 1.3 Free · 129.4s)

_Thinking:_

Mapping row objects to dictionaries for Python Workers by iterating attributes and building dicts.

_Thinking:_



**Tool: bash**

**Input:**
```json
{
  "command": "python3 -c \"\nimport urllib.request, json\n# search github code for to_py in python-workers-examples via api search? try grep via raw files list\n# List all entry files quickly: query-d1, fastapi-todo, flask-todo\nfor path in ['query-d1/src/entry.py','flask-todo/src/worker.py','fastapi-todo/src/worker.py']:\n    url=f'https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/{path}'\n    try:\n        data=urllib.request.urlopen(url).read().decode()\n        print('====',path,'====')\n        print(data[:4000])\n    except Exception as e:\n        print(path, e)\n\"\n"
}
```

**Output:**
```
(no output)

<shell_metadata>
shell tool terminated command after exceeding timeout 120000 ms. If this command is expected to take longer and is not waiting for interactive input, retry with a larger timeout value in milliseconds.
</shell_metadata>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 2.1s)

_Thinking:_



**Tool: webfetch**

**Input:**
```json
{
  "format": "text",
  "url": "https://raw.githubusercontent.com/cloudflare/python-workers-examples/main/flask-todo/src/worker.py"
}
```

**Output:**
```
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from pyodide.ffi import run_sync
from werkzeug.exceptions import HTTPException
from workers import wsgi

app = Flask(__name__)
# Preserve the field order used below rather than sorting keys alphabetically.
app.json.sort_keys = False

# The todobackend.com spec runner calls this Worker from another origin.
CORS(app, origins="*", send_wildcard=True, allow_headers="*", expose_headers="*")


@app.errorhandler(HTTPException)
def _json_error(err: HTTPException):
    """Render Werkzeug's HTTP errors as JSON instead of HTML."""
    return jsonify({"detail": err.name}), err.code


def _base_url() -> str:
    """Return the root URL for the todos collection."""
    return request.url_root.rstrip("/") + "/todos"


def _row_to_todo(row) -> dict:
    """Convert a D1 row into a todo dict with the absolute ``url`` field."""
    return {
        "id": row.id,
        "title": row.title,
        "completed": bool(row.completed),
        "order": row.order,
        "url": f"{_base_url()}/{row.id}",
    }


def _db():
    """Get the D1 database binding from the WSGI environ."""
    return request.environ["workers.env"].DB


@app.get("/todos")
def list_todos():
    results = run_sync(_db().prepare("SELECT * FROM todos").all())
    return jsonify([_row_to_todo(r) for r in results.results])


@app.post("/todos")
def create_todo():
    body = request.get_json(silent=True) or {}
    todo_id = str(uuid.uuid4())
    title = body.get("title", "")
    completed = 1 if body.get("completed", False) else 0
    order = body.get("order")

    run_sync(
        _db()
        .prepare(
            'INSERT INTO todos (id, title, completed, "order") VALUES (?, ?, ?, ?)'
        )
        .bind(todo_id, title, completed, order)
        .run()
    )

    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )

    return jsonify(_row_to_todo(row))


@app.delete("/todos")
def delete_all_todos():
    run_sync(_db().prepare("DELETE FROM todos").run())
    return jsonify([])


@app.get("/todos/<todo_id>")
def get_todo(todo_id: str):
    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )
    if row is None:
        return jsonify({"error": "not found"})
    return jsonify(_row_to_todo(row))


@app.patch("/todos/<todo_id>")
def update_todo(todo_id: str):
    body = request.get_json(silent=True) or {}
    sets = []
    values = []
    if "title" in body:
        sets.append("title = ?")
        values.append(body["title"])
    if "completed" in body:
        sets.append("completed = ?")
        values.append(1 if body["completed"] else 0)
    if "order" in body:
        sets.append('"order" = ?')
        values.append(body["order"])

    if sets:
        values.append(todo_id)
        run_sync(
            _db()
            .prepare(f"UPDATE todos SET {', '.join(sets)} WHERE id = ?")
            .bind(*values)
            .run()
        )

    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )
    if row is None:
        return jsonify({"error": "not found"})
    return jsonify(_row_to_todo(row))


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id: str):
    run_sync(_db().prepare("DELETE FROM todos WHERE id = ?").bind(todo_id).run())
    return jsonify([])


Default = wsgi.entrypoint(app)

```

---

## Assistant (Build · Muse Spark 1.3 Free · 27.4s)

_Thinking:_

Checking canonical DB access pattern and clarifying create_incident return semantics.

_Thinking:_

Choosing re-select by ID after insert and handling a missing row without silent fallback.

_Thinking:_

Simplifying D1 result handling to attribute access with explicit field mapping.

_Thinking:_

Finalizing D1 query paths with attribute access and re-selecting inserted rows.

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/prompt-history"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/prompt-history</path>
<type>directory</type>
<entries>
repository_creation.md
repository_refactor.md

(2 entries)
</entries>
```

**Tool: bash**

**Input:**
```json
{
  "command": "git log --oneline -20; git status; git diff --stat HEAD",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
e37a630 feat: implement repository helpers and refactor incident handling
6031a9c chore: add package.json with wrangler dependency and pyrefly config
39049c5 ignore : add modules and lock files to gitignore
459603b init:add required packages ( initial )
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   wrangler.jsonc

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	migrations/

no changes added to commit (use "git add" and/or "git commit -a")
 wrangler.jsonc | 9 +++++++--
 1 file changed, 7 insertions(+), 2 deletions(-)

```

---

## Assistant (Build · Muse Spark 1.3 Free · 1.9s)

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/prompt-history/repository_creation.md"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/prompt-history/repository_creation.md</path>
<type>file</type>
<content>
1: # D1 repo functions write up
2: 
3: **Session ID:** ses_f1c1e3c00ffeVyNLT710QTz4aR
4: **Created:** 9/27/2026, 10:50:18 PM
5: **Updated:** 9/27/2026, 10:57:05 PM
6: 
7: ---
8: 
9: ## User
10: 
11: using the cloudflare's D1's python compatible async api binding to write repository.py inside src folder
12: 
13: refer the src/schemas.py for knowing what sort of data we are working with . 
14: 
15: task : 
16: - create_incident(db, incident): insert a complete incident record,
17:      then return it only after the insert succeeds.
18:    - get_incident(db, incident_id): return a record or None if absent.
19:    - list_incidents(db, limit=20, offset=0): return records ordered by
20:      created_at DESC, id DESC. 
21: 
22: ---
23: 
24: ## Assistant
25: 
26: **Tool: read**
27: 
28: **Tool: read**
29: 
30: ---
31: 
32: ## Assistant
33: 
34: **Tool: read**
35: 
36: **Tool: glob**
37: 
38: ---
39: 
40: ## Assistant
41: 
42: **Tool: read**
43: 
44: ---
45: 
46: ## Assistant
47: 
48: **Tool: read**
49: 
50: **Tool: read**
51: 
52: **Tool: read**
53: 
54: **Tool: glob**
55: 
56: ---
57: 
58: ## Assistant
59: 
60: **Tool: read**
61: 
62: **Tool: glob**
63: 
64: **Tool: glob**
65: 
66: ---
67: 
68: ## Assistant
69: 
70: **Tool: bash**
71: 
72: ---
73: 
74: ## Assistant
75: 
76: **Tool: bash**
77: 
78: ---
79: 
80: ## Assistant
81: 
82: **Tool: bash**
83: 
84: ---
85: 
86: ## Assistant
87: 
88: **Tool: bash**
89: 
90: ---
91: 
92: ## Assistant
93: 
94: **Tool: bash**
95: 
96: ---
97: 
98: ## Assistant
99: 
100: **Tool: websearch**
101: 
102: ---
103: 
104: ## Assistant
105: 
106: **Tool: webfetch**
107: 
108: **Tool: websearch**
109: 
110: ---
111: 
112: ## Assistant
113: 
114: **Tool: webfetch**
115: 
116: **Tool: webfetch**
117: 
118: ---
119: 
120: ## Assistant
121: 
122: **Tool: webfetch**
123: 
124: **Tool: webfetch**
125: 
126: ---
127: 
128: ## Assistant
129: 
130: **Tool: bash**
131: 
132: ---
133: 
134: ## Assistant
135: 
136: **Tool: bash**
137: 
138: ---
139: 
140: ## Assistant
141: 
142: **Tool: websearch**
143: 
144: ---
145: 
146: ## Assistant
147: 
148: **Tool: websearch**
149: 
150: **Tool: webfetch**
151: 
152: ---
153: 
154: ## Assistant
155: 
156: **Tool: webfetch**
157: 
158: **Tool: webfetch**
159: 
160: ---
161: 
162: ## Assistant
163: 
164: **Tool: bash**
165: 
166: ---
167: 
168: ## Assistant
169: 
170: **Tool: bash**
171: 
172: ---
173: 
174: ## Assistant
175: 
176: **Tool: bash**
177: 
178: ---
179: 
180: ## Assistant
181: 
182: **Tool: bash**
183: 
184: ---
185: 
186: ## Assistant
187: 
188: **Tool: bash**
189: 
190: ---
191: 
192: ## Assistant
193: 
194: **Tool: read**
195: 
196: **Tool: read**
197: 
198: ---
199: 
200: ## Assistant
201: 
202: **Tool: write**
203: 
204: ---
205: 
206: ## Assistant
207: 
208: **Tool: bash**
209: 
210: ---
211: 
212: ## Assistant
213: 
214: **Tool: edit**
215: 
216: ---
217: 
218: ## Assistant
219: 
220: **Tool: bash**
221: 
222: ---
223: 
224: ## Assistant
225: 
226: **Tool: bash**
227: 
228: ---
229: 
230: ## Assistant
231: 
232: **Tool: bash**
233: 
234: ---
235: 
236: ## Assistant
237: 
238: **Tool: bash**
239: 
240: ---
241: 
242: ## Assistant
243: 
244: **Tool: read**
245: 
246: ---
247: 
248: ## Assistant
249: 
250: **Tool: edit**
251: 
252: ---
253: 
254: ## Assistant
255: 
256: **Tool: edit**
257: 
258: ---
259: 
260: ## Assistant
261: 
262: **Tool: read**
263: 
264: ---
265: 
266: ## Assistant
267: 
268: **Tool: edit**
269: 
270: ---
271: 
272: ## Assistant
273: 
274: **Tool: bash**
275: 
276: ---
277: 
278: ## Assistant
279: 
280: **Tool: bash**
281: 
282: ---
283: 
284: ## Assistant
285: 
286: **Tool: read**
287: 
288: ---
289: 
290: ## Assistant
291: 
292: Created `src/repository.py` using the D1 Python Workers async binding API (`db.prepare(...).bind(...).run()/all()/first()`, all awaited):
293: 
294: - `create_incident(db, incident)`: extracts `title/symptoms/environment` from `IncidentCreate` (attribute / `model_dump()` / mapping / tuple), `INSERT INTO incidents ...` + `await run()`, checks `success`, then `SELECT ... WHERE id = ?` via `meta.last_row_id` + `await first()`. Raises on explicit failure.
295: - `get_incident(db, incident_id)`: `SELECT id, title, symptoms, environment, created_at ... WHERE id = ? LIMIT 1` + `first()`, returns `dict` or `None`.
296: - `list_incidents(db, limit=20, offset=0)`: `SELECT ... ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?` + `all()` (fallback to `run()`, which D1 aliases).
297: 
298: Returns plain `dict`s, handles real D1 rows (attribute-style `row.id`, `result.results`, `result.meta.last_row_id`, `to_py()` JsProxy) and dict-style mocks. Verified against attribute-style fake D1, dict-style sqlite shim, and `pyrefly check` (0 errors).
299: 
300: Note: `src/schemas.py` mixes `model_config` and `class Config`, which Pydantic rejects — repository import is guarded so it still imports, but you may want to fix the schema.
301: 
302: ---
303: 
304: ## User
305: 
306: Check the pydantic schema see if the model config contradicts each other
307: 
308: ---
309: 
310: ## Assistant
311: 
312: **Tool: read**
313: 
314: ---
315: 
316: ## Assistant
317: 
318: **Tool: bash**
319: 
320: ---
321: 
322: ## Assistant
323: 
324: **Tool: edit**
325: 
326: ---
327: 
328: ## Assistant
329: 
330: **Tool: bash**
331: 
332: ---
333: 
334: ## Assistant
335: 
336: Yes — it contradicted itself:
337: 
338: - `model_config = ConfigDict(...)` is Pydantic v2 style
339: - `class Config: schema_extra = ...` is Pydantic v1 style
340: 
341: Pydantic forbids mixing them (`PydanticUserError: "Config" and "model_config" cannot be used together`), and `schema_extra` is itself stale in v2 (renamed `json_schema_extra`).
342: 
343: Fixed `src/schemas.py:4-21` by folding the example into the single v2 config and deleting `class Config`:
344: 
345: ```python
346: model_config = ConfigDict(
347:     str_strip_whitespace=True,
348:     extra="forbid",
349:     json_schema_extra={"example": {...}},
350: )
351: ```
352: 
353: Verified: import works, whitespace-stripping + `extra="forbid"` preserved, example still in `model_json_schema()`, `pyrefly check` 0 errors.
354: 
355: ---
356: 

(End of file - total 356 lines)
</content>
```

**Tool: read**

**Input:**
```json
{
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/prompt-history/repository_refactor.md"
}
```

**Output:**
```
<path>/home/akhileshmt/Documents/Fun/wtf-error/prompt-history/repository_refactor.md</path>
<type>file</type>
<content>
1: # Refactor repository.py into class methods
2: 
3: **Session ID:** ses_f1c107bfdffe66ZQORIi6Iq7Xa
4: **Created:** 9/27/2026, 11:05:20 PM
5: **Updated:** 9/27/2026, 11:06:40 PM
6: 
7: ---
8: 
9: ## User
10: 
11: refactor the repository.py with the internal helper function into a class and static methods and then for the incident related functions call the methods.
12: 
13: ---
14: 
15: ## Assistant
16: 
17: **Tool: glob**
18: 
19: ---
20: 
21: ## Assistant
22: 
23: **Tool: read**
24: 
25: ---
26: 
27: ## Assistant
28: 
29: **Tool: grep**
30: 
31: ---
32: 
33: ## Assistant
34: 
35: **Tool: glob**
36: 
37: ---
38: 
39: ## Assistant
40: 
41: **Tool: read**
42: 
43: **Tool: read**
44: 
45: ---
46: 
47: ## Assistant
48: 
49: **Tool: read**
50: 
51: ---
52: 
53: ## Assistant
54: 
55: **Tool: read**
56: 
57: ---
58: 
59: ## Assistant
60: 
61: **Tool: todowrite**
62: 
63: ---
64: 
65: ## Assistant
66: 
67: **Tool: edit**
68: 
69: ---
70: 
71: ## Assistant
72: 
73: **Tool: read**
74: 
75: ---
76: 
77: ## Assistant
78: 
79: **Tool: todowrite**
80: 
81: ---
82: 
83: ## Assistant
84: 
85: **Tool: edit**
86: 
87: ---
88: 
89: ## Assistant
90: 
91: **Tool: edit**
92: 
93: ---
94: 
95: ## Assistant
96: 
97: **Tool: read**
98: 
99: ---
100: 
101: ## Assistant
102: 
103: **Tool: bash**
104: 
105: ---
106: 
107: ## Assistant
108: 
109: **Tool: bash**
110: 
111: ---
112: 
113: ## Assistant
114: 
115: **Tool: todowrite**
116: 
117: ---
118: 
119: ## Assistant
120: 
121: Refactored `src/repository.py:33`:
122: 
123: * Added `RepositoryHelpers` class with 9 `@staticmethod` helpers: `_incident_fields`, `_maybe_to_py`, `_row_to_dict`, `_result_rows`, `_is_success`, `_coerce_row_id`, `_last_row_id`, `_execute_run`, `_fetch_all`.
124: * Internal cross-calls now use `RepositoryHelpers.*`.
125: * `create_incident`, `get_incident`, `list_incidents` kept as module-level public API but now call `RepositoryHelpers.*`.
126: 
127: Verified: `py_compile` passes, all 9 are `staticmethod`s, and fake-D1 smoke test for create/get/list passes.
128: 
129: ---
130: 

(End of file - total 130 lines)
</content>
```

---

## Assistant (Build · Muse Spark 1.3 Free · 37.3s)

_Thinking:_

Evaluating return semantics for create_incident and choosing between refetching the record or returning the input dict.

_Thinking:_

Switching to a fetch-by-ID read after insert to avoid race conditions.

_Thinking:_

Choosing to return the inserted input dict instead of re-querying to avoid hidden errors.

_Thinking:_

Switching create_incident to return the input dict and updating get and list to convert rows to plain dicts.

_Thinking:_

Removing the helper class and inlining row conversion to keep exactly three async functions.

_Thinking:_



**Tool: write**

**Input:**
```json
{
  "content": "\"\"\"Repository helpers for incident records stored in Cloudflare D1.\n\nUses the D1 Python Workers async binding API (see\nhttps://developers.cloudflare.com/d1/worker-api/prepared-statements and\nhttps://developers.cloudflare.com/d1/examples/query-d1-from-python-workers):\n\n    await db.prepare(\"INSERT INTO ...\").bind(...).run()\n    await db.prepare(\"SELECT ... WHERE id = ?\").bind(...).first()\n    await db.prepare(\"SELECT ...\").bind(...).all()\n\n``db`` is the D1 database binding (e.g. ``env.DB`` or, inside FastAPI,\n``request.scope[\"env\"].DB``).\n\nPer the Python Workers FFI, D1 rows come back as JavaScript objects\nproxied into Python, so columns are read via attribute access\n(``row.id``, ``row.title``, ...) as in the official\n``fastapi-todo`` / ``query-d1`` examples. ``all()`` returns a\n``D1Result`` whose ``results`` attribute is the list of rows, and\n``first()`` returns a single row object or ``None`` when no row matches.\nResults are converted here into plain Python ``dict`` / ``list`` objects\nso they are JSON-serializable.\n\nAll queries use parameterized SQL (``?`` placeholders + ``bind()``).\nErrors are never swallowed: if D1 fails or conversion fails the\nexception propagates to the caller.\n\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import Any\n\nCOLUMNS = \"id, title, symptoms, environment, status, created_at, updated_at\"\n\n\nasync def create_incident(db: Any, incident: dict[str, Any]) -> dict[str, Any]:\n    \"\"\"Insert a complete incident record and return it.\n\n    ``incident`` is already a complete dictionary containing all 7 fields\n    (``id``, ``title``, ``symptoms``, ``environment``, ``status``,\n    ``created_at``, ``updated_at``). The caller provides the ID, status,\n    and timestamps -- nothing is generated here.\n    \"\"\"\n    await (\n        db.prepare(\n            \"INSERT INTO incidents \"\n            \"(id, title, symptoms, environment, status, created_at, updated_at) \"\n            \"VALUES (?, ?, ?, ?, ?, ?, ?)\"\n        )\n        .bind(\n            incident[\"id\"],\n            incident[\"title\"],\n            incident[\"symptoms\"],\n            incident[\"environment\"],\n            incident[\"status\"],\n            incident[\"created_at\"],\n            incident[\"updated_at\"],\n        )\n        .run()\n    )\n    return dict(incident)\n\n\nasync def get_incident(db: Any, incident_id: str) -> dict[str, Any] | None:\n    \"\"\"Return a single incident as a plain dict, or None if absent.\"\"\"\n    row = (\n        await db.prepare(\n            f\"SELECT {COLUMNS} FROM incidents WHERE id = ? LIMIT 1\"\n        )\n        .bind(incident_id)\n        .first()\n    )\n    if row is None:\n        return None\n    return {\n        \"id\": row.id,\n        \"title\": row.title,\n        \"symptoms\": row.symptoms,\n        \"environment\": row.environment,\n        \"status\": row.status,\n        \"created_at\": row.created_at,\n        \"updated_at\": row.updated_at,\n    }\n\n\nasync def list_incidents(\n    db: Any, limit: int = 20, offset: int = 0\n) -> list[dict[str, Any]]:\n    \"\"\"Return incidents ordered by created_at DESC, id DESC.\"\"\"\n    result = (\n        await db.prepare(\n            f\"SELECT {COLUMNS} FROM incidents \"\n            \"ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?\"\n        )\n        .bind(limit, offset)\n        .all()\n    )\n    return [\n        {\n            \"id\": row.id,\n            \"title\": row.title,\n            \"symptoms\": row.symptoms,\n            \"environment\": row.environment,\n            \"status\": row.status,\n            \"created_at\": row.created_at,\n            \"updated_at\": row.updated_at,\n        }\n        for row in result.results\n    ]\n",
  "filePath": "/home/akhileshmt/Documents/Fun/wtf-error/src/repository.py"
}
```

**Output:**
```
Wrote file successfully.
```

---

## Assistant (Build · Muse Spark 1.3 Free · 3.8s)

_Thinking:_



**Tool: bash**

**Input:**
```json
{
  "command": "python3 -m py_compile src/repository.py && echo COMPILE_OK && grep -rn \"last_row_id\\|RepositoryHelpers\\|_maybe_to_py\\|_row_to_dict\\|_result_rows\\|ORDER BY id DESC LIMIT 1\" src/repository.py || echo \"CLEAN: no banned patterns\"",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
COMPILE_OK
CLEAN: no banned patterns

```

---

## Assistant (Build · Muse Spark 1.3 Free · 10.1s)

**Tool: bash**

**Input:**
```json
{
  "command": "python3 - <<'PY'\nimport asyncio, sys\nsys.path.insert(0, \"src\")\nimport repository as r\nimport inspect\n\n# 1. Only 3 functions?\nfns = [m for m in dir(r) if not m.startswith(\"_\")]\nprint(\"public attrs:\", fns)\nassert hasattr(r, \"create_incident\") and hasattr(r, \"get_incident\") and hasattr(r, \"list_incidents\")\n# ensure no RepositoryHelpers class\nassert not hasattr(r, \"RepositoryHelpers\"), \"RepositoryHelpers should be removed\"\nsrc = open(\"src/repository.py\").read()\nassert \"last_row_id\" not in src\nassert \"to_py\" not in src\nassert \"ORDER BY id DESC LIMIT 1\" not in src\nprint(\"structure OK\")\nprint(\"funcs:\", [n for n in [\"create_incident\",\"get_incident\",\"list_incidents\"]])\n\n# 2. Realistic fake D1 binding (attribute-style rows, like fastapi-todo example)\nclass Row:\n    def __init__(self, **kw): self.__dict__.update(kw)\n\nclass Statement:\n    def __init__(self, db, sql):\n        self.db, self.sql, self.args = db, sql, ()\n    def bind(self, *args):\n        self.args = args\n        return self\n    async def run(self):\n        self.db.calls.append((\"run\", self.sql, self.args))\n        # simulate INSERT storing\n        if self.sql.startswith(\"INSERT\"):\n            cols = [\"id\",\"title\",\"symptoms\",\"environment\",\"status\",\"created_at\",\"updated_at\"]\n            self.db.store[self.args[0]] = dict(zip(cols, self.args))\n            return Row(success=True, meta=Row(last_row_id=0))\n        raise AssertionError(\"run called for non-insert: \" + self.sql)\n    async def first(self):\n        self.db.calls.append((\"first\", self.sql, self.args))\n        if \"WHERE id = ?\" in self.sql:\n            rec = self.db.store.get(self.args[0])\n            return Row(**rec) if rec else None\n        raise AssertionError(\"unexpected first: \" + self.sql)\n    async def all(self):\n        self.db.calls.append((\"all\", self.sql, self.args))\n        assert \"ORDER BY created_at DESC, id DESC\" in self.sql, self.sql\n        assert \"LIMIT ? OFFSET ?\" in self.sql, self.sql\n        limit, offset = self.args\n        rows = sorted(self.db.store.values(), key=lambda d: (d[\"created_at\"], d[\"id\"]), reverse=True)\n        rows = rows[offset:offset+limit]\n        R = Row(success=True, meta=Row())\n        R.results = [Row(**d) for d in rows]\n        return R\n\nclass FakeDB:\n    def __init__(self): self.store={}; self.calls=[]\n    def prepare(self, sql):\n        self.calls.append((\"prepare\", sql))\n        return Statement(self, sql)\n\nasync def main():\n    db = FakeDB()\n    inc = {\"id\":\"abc\",\"title\":\"t\",\"symptoms\":\"s\",\"environment\":\"e\",\"status\":\"open\",\"created_at\":\"2026-09-27T00:00:00Z\",\"updated_at\":\"2026-09-27T00:00:00Z\"}\n    out = await r.create_incident(db, inc)\n    print(\"create returned:\", out)\n    assert out == inc and out is not inc, \"should return copy of incident dict\"\n    assert isinstance(out, dict)\n    # check INSERT used 7 placeholders and all fields\n    ins = [c for c in db.calls if c[0]==\"run\"][0]\n    print(\"insert sql:\", ins[1])\n    assert ins[1].count(\"?\") == 7\n    for col in [\"id\",\"title\",\"symptoms\",\"environment\",\"status\",\"created_at\",\"updated_at\"]:\n        assert col in ins[1], col\n    # no SELECT after insert (no fallback, no last_row_id fetch)\n    assert not any(c[0]==\"first\" for c in db.calls), f\"create should not SELECT, calls={db.calls}\"\n\n    # get existing\n    row = await r.get_incident(db, \"abc\")\n    print(\"get:\", row)\n    assert row == inc and isinstance(row, dict)\n    # get missing\n    row2 = await r.get_incident(db, \"nope\")\n    assert row2 is None\n    print(\"get missing -> None OK\")\n\n    # list ordering\n    await r.create_incident(db, {\"id\":\"b\",\"title\":\"t\",\"symptoms\":\"s\",\"environment\":\"e\",\"status\":\"open\",\"created_at\":\"2026-09-28T00:00:00Z\",\"updated_at\":\"2026-09-28T00:00:00Z\"})\n    await r.create_incident(db, {\"id\":\"a\",\"title\":\"t\",\"symptoms\":\"s\",\"environment\":\"e\",\"status\":\"open\",\"created_at\":\"2026-09-28T00:00:00Z\",\"updated_at\":\"2026-09-28T00:00:00Z\"})\n    lst = await r.list_incidents(db)\n    print(\"list ids:\", [d[\"id\"] for d in lst])\n    assert [d[\"id\"] for d in lst] == [\"b\",\"a\",\"abc\"], \"ORDER BY created_at DESC, id DESC\"\n    assert all(isinstance(d, dict) for d in lst)\n    assert set(lst[0].keys()) == {\"id\",\"title\",\"symptoms\",\"environment\",\"status\",\"created_at\",\"updated_at\"}\n    # limit/offset\n    lst2 = await r.list_incidents(db, limit=1, offset=1)\n    assert [d[\"id\"] for d in lst2] == [\"a\"]\n    print(\"limit/offset OK\")\n\n    # errors propagate (do not hide)\n    class BadDB(FakeDB):\n        def prepare(self, sql): raise RuntimeError(\"D1 down\")\n    try:\n        await r.get_incident(BadDB(), \"x\")\n        raise AssertionError(\"should have raised\")\n    except RuntimeError as e:\n        assert \"D1 down\" in str(e)\n        print(\"error propagation OK\")\n\nasyncio.run(main())\nprint(\"ALL CHECKS PASSED\")\nPY",
  "workdir": "/home/akhileshmt/Documents/Fun/wtf-error"
}
```

**Output:**
```
public attrs: ['Any', 'COLUMNS', 'annotations', 'create_incident', 'get_incident', 'list_incidents']
structure OK
funcs: ['create_incident', 'get_incident', 'list_incidents']
create returned: {'id': 'abc', 'title': 't', 'symptoms': 's', 'environment': 'e', 'status': 'open', 'created_at': '2026-09-27T00:00:00Z', 'updated_at': '2026-09-27T00:00:00Z'}
insert sql: INSERT INTO incidents (id, title, symptoms, environment, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)
get: {'id': 'abc', 'title': 't', 'symptoms': 's', 'environment': 'e', 'status': 'open', 'created_at': '2026-09-27T00:00:00Z', 'updated_at': '2026-09-27T00:00:00Z'}
get missing -> None OK
list ids: ['b', 'a', 'abc']
limit/offset OK
error propagation OK
ALL CHECKS PASSED

```

---

## Assistant (Build · Muse Spark 1.3 Free · 15.3s)

_Thinking:_

Weighing whether to return the inserted dict or fetch by ID to satisfy the test requirement.

Cleaned up `src/repository.py` to match the `incidents` table exactly.

- Table fields: `id, title, symptoms, environment, status, created_at, updated_at` (`src/repository.py:19`, `migrations/0001_create_incidents.sql:2-13`).
- Only 3 functions remain: `create_incident`, `get_incident`, `list_incidents`. Removed `RepositoryHelpers`, `last_row_id` logic, latest-row fallback, and all mock/dict/JsProxy gymnastics.
- `create_incident(db, incident)`: parameterized `INSERT` of all 7 caller-provided fields via `prepare(...).bind(...).run()`, then `return dict(incident)`. No ID/status/timestamp generation, no `SELECT` fallback (avoids the race).
- `get_incident`: `SELECT ... WHERE id = ? LIMIT 1` + `first()`, attribute access (`row.id`, etc. per official `fastapi-todo`/`query-d1` examples) into a plain `dict`, `None` if absent.
- `list_incidents`: `SELECT ... ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?` + `all()`, `result.results` mapped to plain `list[dict]`.
- Per Cloudflare D1 docs (`prepare`/`bind`/`run`/`all`/`first`, `D1Result.results`, Python FFI attribute access): no `to_py()` branches, no `try/except` — D1/conversion errors propagate.

Verified with attribute-style fake D1: insert uses 7 placeholders, get/list return plain dicts, ordering and `limit`/`offset` work, errors propagate.

---

