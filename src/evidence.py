"""Redact common credentials and give pasted evidence stable line IDs."""

from __future__ import annotations

import re

_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_ASSIGNMENT = re.compile(
    r"(?i)(\b[\w.-]*(?:api[_-]?key|access[_-]?key|client[_-]?secret|"
    r"database[_-]?url|connection[_-]?string|password|passwd|secret|"
    r"token|authorization)\b\s*[:=]\s*)"
    r"(['\"]?)([^\s,;&'\"]+)(['\"]?)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")
_TOKEN = re.compile(
    r"\b(?:AKIA[0-9A-Z]{16}|gh[opusr]_[A-Za-z0-9_]{20,}|"
    r"xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9_-]{20,})\b"
)
_URL_PASSWORD = re.compile(r"(?i)(://[^:/\s]+:)[^@/\s]+(@)")


def prepare_evidence(content: str, evidence_id: str) -> tuple[str, list[str]]:
    """Return redacted, line-labelled evidence and its valid line IDs."""
    content = redact_secrets(content)

    lines = content.splitlines() or [""]
    line_ids = [f"{evidence_id}-L{number:03d}" for number in range(1, len(lines) + 1)]
    labelled = "\n".join(
        f"[{line_id}] {line}" for line_id, line in zip(line_ids, lines, strict=True)
    )
    return labelled, line_ids


def redact_secrets(content: str) -> str:
    content = content.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    content = _PRIVATE_KEY.sub("[REDACTED PRIVATE KEY]", content)
    content = _URL_PASSWORD.sub(r"\1[REDACTED]\2", content)
    content = _BEARER.sub("Bearer [REDACTED]", content)
    content = _TOKEN.sub("[REDACTED TOKEN]", content)
    return _ASSIGNMENT.sub(r"\1\2[REDACTED]\4", content)
