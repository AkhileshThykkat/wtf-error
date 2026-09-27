-- Preserve existing findings while adding stable evidence references.
ALTER TABLE findings ADD COLUMN evidence_line_ids TEXT NOT NULL DEFAULT '[]';

CREATE TABLE evidence (
    id TEXT PRIMARY KEY NOT NULL,
    incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_evidence_incident_created_id
    ON evidence (incident_id, created_at ASC, id ASC);
