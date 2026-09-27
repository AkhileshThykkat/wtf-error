"""Orchestration-only incident investigation service (first version).

Pipeline::

    incident + history
            ↓
    build context
            ↓
    Workers AI (one model call)
            ↓
    structured investigation result

Deliberately out of scope here: API routes, raw SQL, persistence of the
AI response, retries, loops, tool calling, agents, background jobs, RAG,
embeddings. Workers AI errors are allowed to propagate to the caller.

Workers AI call shape
---------------------
The AI-specific code lives only in :func:`run_model` and follows the
documented binding behavior:

* ``await env.AI.run(model, {"messages": [...]})`` for chat models such
  as ``@cf/meta/llama-3.1-8b-instruct`` (see
  https://developers.cloudflare.com/workers-ai/configuration/bindings/
  and https://developers.cloudflare.com/workers-ai/features/prompting/).
* In Python Workers the call is ``await ai.run(model, {...})`` with a
  plain Python dict -- no ``to_js`` glue needed since Python Workers GA
  (see https://blog.cloudflare.com/python-workers-ga/, whose FastAPI
  example calls ``await env.AI.run(...)`` directly).
* Chat-completions style calls return an object shaped like
  ``{"response": "<generated text>"}`` (see the model pages under
  https://developers.cloudflare.com/workers-ai/models/, e.g.
  llama-3.1-8b-instruct documents a ``response`` string field). Through
  the Python FFI the response is attribute-style, i.e.
  ``resp.response`` (see
  ``src/cloudflare/internal/test/ai/ai-api-test.py`` in cloudflare/workerd).
  :func:`run_model` therefore accepts both attribute-style and
  dict-style responses.
"""

from __future__ import annotations

import json
from typing import Any

from repository import get_incident
from repository import list_findings as list_findings_from_db
from repository import list_messages as list_messages_from_db

#: Chat model used for the single investigation call. Kept as a module
#: constant (and overridable per call) so the model choice stays
#: configuration, not logic scattered through the service.
DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct"

SYSTEM_PROMPT = (
    "You are investigating a software/system incident. "
    "Analyze the symptoms, identify likely causes, explain your reasoning "
    "briefly, and suggest what should be checked next. "
    "Do not claim anything was verified when it was not. "
    'Respond with JSON only, using exactly these keys: "analysis" (string), '
    '"possible_causes" (array of strings), "next_steps" (array of strings).'
)


class IncidentNotFoundError(ValueError):
    """Raised when no incident exists for the requested id."""


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
) -> list[dict[str, str]]:
    """Build the ``messages`` payload sent to Workers AI.

    Keeps the full incident record (title, symptoms, environment, status),
    the previous messages (role + content only) and the existing findings
    (title + detail only) so the model sees the whole investigation state.
    """
    user_content = (
        f"Incident title: {incident.get('title', '')}\n"
        f"Symptoms: {incident.get('symptoms', '')}\n"
        f"Environment: {incident.get('environment', '')}\n"
        f"Status: {incident.get('status', '')}\n"
        f"\nPrevious messages:\n{_format_messages(history)}\n"
        f"\nExisting findings:\n{_format_findings(findings)}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


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


def parse_investigation_text(text: str) -> dict[str, Any]:
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
    return {
        "analysis": analysis,
        "possible_causes": possible_causes,
        "next_steps": next_steps,
    }


async def run_model(
    ai: Any, model: str, messages: list[dict[str, str]]
) -> str:
    """Make the single Workers AI call and return the generated text.

    This is the only Workers AI-specific function. ``ai`` is the Workers
    AI binding (``env.AI``); ``messages`` uses the documented scoped-prompt
    shape ``[{"role": ..., "content": ...}]``. Any binding/model error
    propagates unchanged.
    """
    response = await ai.run(model, {"messages": messages})
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
    3. Build the Workers AI context.
    4. Make one model call.
    5. Return the structured result ``{"analysis", "possible_causes",
       "next_steps"}``.

    Nothing is written to ``messages`` or ``findings`` here.
    """
    incident = await get_incident(db, incident_id)
    if incident is None:
        raise IncidentNotFoundError(f"Incident not found: {incident_id}")
    history = await list_messages_from_db(db, incident_id)
    findings = await list_findings_from_db(db, incident_id)
    messages = build_investigation_messages(incident, history, findings)
    raw_text = await run_model(ai, model, messages)
    return parse_investigation_text(raw_text)
