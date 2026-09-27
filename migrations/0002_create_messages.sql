-- Migration number: 0002 	 2026-09-27T18:00:00.000Z
CREATE TABLE messages (
    id TEXT PRIMARY KEY NOT NULL,
    incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
    role TEXT NOT NULL
        CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_messages_incident_created_id
    ON messages (incident_id, created_at ASC, id ASC);
