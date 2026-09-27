-- Migration number: 0001 	 2026-09-27T17:51:00.221Z
CREATE TABLE incidents (
    id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    environment TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'investigating', 'resolved')),

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_incidents_created_at_id
    ON incidents (created_at DESC, id DESC);