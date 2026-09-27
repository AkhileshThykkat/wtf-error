"""Incident investigation orchestration and persistence.

Pipeline::

    incident + evidence + history
            ↓
    build context
            ↓
    Workers AI (one model call)
            ↓
    validate and persist messages and findings

Workers AI call shape
---------------------
The AI-specific code lives only in :func:`run_model` and follows the
documented binding behavior:

* ``await env.AI.run(model, {"messages": [...]})`` for chat models such
  as ``@cf/meta/llama-3.3-70b-instruct-fp8-fast`` (see
  https://developers.cloudflare.com/workers-ai/configuration/bindings/
  and https://developers.cloudflare.com/workers-ai/features/prompting/).
* In Python Workers the call is ``await ai.run(model, {...})`` with a
  plain Python dict -- no ``to_js`` glue needed since Python Workers GA
  (see https://blog.cloudflare.com/python-workers-ga/, whose FastAPI
  example calls ``await env.AI.run(...)`` directly).
* Chat-completions style calls return an object shaped like
  ``{"response": "<generated text>"}`` (see the model pages under
  https://developers.cloudflare.com/workers-ai/models/, e.g.
  the selected model documents a ``response`` string field). Through
  the Python FFI the response is attribute-style, i.e.
  ``resp.response`` (see
  ``src/cloudflare/internal/test/ai/ai-api-test.py`` in cloudflare/workerd).
  :func:`run_model` therefore accepts both attribute-style and
  dict-style responses.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from repository import get_incident
from repository import create_finding, create_message
from repository import list_evidence as list_evidence_from_db
from repository import list_findings as list_findings_from_db
from repository import list_messages as list_messages_from_db

#: Chat model used for the single investigation call. Kept as a module
#: constant (and overridable per call) so the model choice stays
#: configuration, not logic scattered through the service.
DEFAULT_MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

SYSTEM_PROMPT = (
    "You are investigating a software/system incident. "
    "Analyze the symptoms, identify likely causes, explain your reasoning "
    "briefly, and suggest what should be checked next. "
    "Do not claim anything was verified when it was not. "
    "Use only the supplied evidence. Cite its line IDs in each finding and "
    "never invent evidence. If evidence is insufficient, say so clearly. "
    'Respond with JSON only: "analysis" (string), "possible_causes" '
    '(array of strings), "next_steps" (array of strings), and "findings" '
    '(array of objects with "title", "detail", and "evidence_line_ids").'
)


class IncidentNotFoundError(ValueError):
    """Raised when no incident exists for the requested id."""


class WorkersAIRequestError(RuntimeError):
    """Raised when the Workers AI binding cannot complete an inference call."""


def _format_messages(history: list[dict[str, Any]]) -> str:
    if not history:
        return "(none)"
    return "\n".join(
        f"- {m.get('role', '?')}: {m.get('content', '')}" for m in history
    )


def _format_findings(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "(none)"
    return "\n".join(
        f"- {f.get('title', '')}: {f.get('detail', '')}" for f in findings
    )


def build_investigation_messages(
    incident: dict[str, Any],
    history: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    evidence: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build the ``messages`` payload sent to Workers AI.

    Includes the incident, conversation, existing findings, and redacted,
    line-labelled evidence so the model sees the current investigation state.
    """
    user_content = (
        f"Incident title: {incident.get('title', '')}\n"
        f"Symptoms: {incident.get('symptoms', '')}\n"
        f"Environment: {incident.get('environment', '')}\n"
        f"Status: {incident.get('status', '')}\n"
        f"\nPrevious messages:\n{_format_messages(history)}\n"
        f"\nExisting findings:\n{_format_findings(findings)}\n"
        f"\nRedacted evidence with stable line IDs:\n"
        f"{_format_evidence(evidence or [])}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def _format_evidence(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "(none)"
    return "\n".join(
        f"Source: {item.get('source', 'Evidence')}\n{item.get('content', '')}"
        for item in evidence
    )


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()
        # Allow a leading language tag such as ```json
        if "\n" in text:
            first_line, _, rest = text.partition("\n")
            if first_line.strip() and not first_line.strip().startswith("{"):
                text = rest.strip()
    return text


def parse_investigation_text(
    text: str, valid_evidence_line_ids: set[str] | None = None
) -> dict[str, Any]:
    """Parse the model's raw text into the structured investigation result.

    Raises ``ValueError`` with the raw text attached when the model did
    not return the expected JSON shape -- never silently returns a guess.
    """
    cleaned = _strip_code_fences(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Workers AI did not return valid JSON: {exc}; raw text: {text!r}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"Workers AI must return a JSON object; raw text: {text!r}"
        )
    if set(data) != {"analysis", "possible_causes", "next_steps", "findings"}:
        raise ValueError("Workers AI result must contain exactly the required keys")
    analysis = data.get("analysis")
    possible_causes = data.get("possible_causes")
    next_steps = data.get("next_steps")
    if not isinstance(analysis, str) or not analysis.strip():
        raise ValueError(
            "Workers AI result is missing a non-empty 'analysis' string; "
            f"raw text: {text!r}"
        )
    if not isinstance(possible_causes, list) or not all(
        isinstance(c, str) for c in possible_causes
    ):
        raise ValueError(
            "Workers AI result 'possible_causes' must be an array of strings; "
            f"raw text: {text!r}"
        )
    if not isinstance(next_steps, list) or not all(
        isinstance(s, str) for s in next_steps
    ):
        raise ValueError(
            "Workers AI result 'next_steps' must be an array of strings; "
            f"raw text: {text!r}"
        )
    result = {
        "analysis": analysis,
        "possible_causes": possible_causes,
        "next_steps": next_steps,
    }
    model_findings = data["findings"]
    if not isinstance(model_findings, list) or len(model_findings) > 20:
        raise ValueError("Workers AI result 'findings' must be an array of at most 20")
    findings: list[dict[str, Any]] = []
    for finding in model_findings:
        if not isinstance(finding, dict) or set(finding) != {
            "title", "detail", "evidence_line_ids"
        }:
            raise ValueError("Each finding must contain exactly the required fields")
        title = finding["title"]
        detail = finding["detail"]
        evidence_ids = finding["evidence_line_ids"]
        if not isinstance(title, str) or not title.strip() or len(title) > 160:
            raise ValueError("Each finding needs a title of at most 160 characters")
        if not isinstance(detail, str) or not detail.strip() or len(detail) > 4000:
            raise ValueError("Each finding needs detail of at most 4000 characters")
        if not isinstance(evidence_ids, list) or not all(
            isinstance(line_id, str) for line_id in evidence_ids
        ):
            raise ValueError("Finding evidence_line_ids must be an array of strings")
        if valid_evidence_line_ids is not None and not set(
            evidence_ids
        ).issubset(valid_evidence_line_ids):
            raise ValueError("A finding references an unknown evidence line ID")
        findings.append(
            {
                "title": title.strip(),
                "detail": detail.strip(),
                "evidence_line_ids": list(dict.fromkeys(evidence_ids)),
            }
        )
    result["findings"] = findings
    return result


async def run_model(
    ai: Any, model: str, messages: list[dict[str, str]]
) -> str:
    """Make the single Workers AI call and return the generated text.

    This is the only Workers AI-specific function. ``ai`` is the Workers
    AI binding (``env.AI``); ``messages`` uses the documented scoped-prompt
    shape ``[{"role": ..., "content": ...}]``. Binding errors are wrapped
    as :class:`WorkersAIRequestError` for the API layer.
    """
    try:
        response = await ai.run(model, {"messages": messages})
    except Exception as exc:
        raise WorkersAIRequestError("Workers AI request failed") from exc
    text: Any = getattr(response, "response", None)
    if text is None and isinstance(response, dict):
        text = response.get("response")
    if text is None and hasattr(response, "get"):
        try:
            text = response.get("response")  # type: ignore[union-attr]
        except Exception:
            text = None
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "Workers AI returned an empty response "
            f"for model {model!r}: {response!r}"
        )
    return text


async def investigate_incident(
    db: Any,
    ai: Any,
    incident_id: str,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Run one investigation pass for an incident.

    1. Load the incident via the repository; raise
       :class:`IncidentNotFoundError` when absent.
    2. Load previous messages and existing findings via the repository.
    3. Load the evidence and build the Workers AI context.
    4. Make one model call.
    5. Validate line references and persist the assistant response and findings.
    """
    incident = await get_incident(db, incident_id)
    if incident is None:
        raise IncidentNotFoundError(f"Incident not found: {incident_id}")
    history = await list_messages_from_db(db, incident_id)
    findings = await list_findings_from_db(db, incident_id)
    evidence = await list_evidence_from_db(db, incident_id)
    messages = build_investigation_messages(incident, history, findings, evidence)
    raw_text = await run_model(ai, model, messages)
    valid_line_ids = {
        line.partition("]")[0][1:]
        for item in evidence
        for line in item["content"].splitlines()
        if line.startswith("[") and "]" in line
    }
    result = parse_investigation_text(raw_text, valid_line_ids)
    now = datetime.now(timezone.utc).isoformat()
    await create_message(
        db,
        {
            "id": str(uuid4()),
            "incident_id": incident_id,
            "role": "assistant",
            "content": json.dumps(result, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        },
    )
    for finding in result.get("findings", []):
        await create_finding(
            db,
            {
                "id": str(uuid4()),
                "incident_id": incident_id,
                **finding,
                "created_at": now,
            },
        )
    return result
