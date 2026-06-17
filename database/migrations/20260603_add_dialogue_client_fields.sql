USE smart_home_aiot;

ALTER TABLE dialogue_sessions
ADD COLUMN client_id VARCHAR(100) NULL AFTER session_id,
ADD COLUMN source VARCHAR(30) NULL AFTER client_id;

CREATE INDEX idx_dialogue_client_status_updated
ON dialogue_sessions (client_id, status, updated_at);