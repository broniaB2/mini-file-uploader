-- Railway Postgres schema for this assignment.
-- You can paste this directly into your report.

CREATE TABLE IF NOT EXISTS uploaded_files (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(512) NOT NULL,
  content_type VARCHAR(256),
  data BYTEA NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

