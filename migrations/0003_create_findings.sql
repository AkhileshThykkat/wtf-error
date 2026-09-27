-- Migration number: 0003 	 2026-09-27T18:00:00.000Z
CREATE TABLE findings (
    id TEXT PRIMARY KEY NOT NULL,
    incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_findings_incident_created_id
    ON findings (incident_id, created_at ASC, id ASC);
