Database Integration Guide — Aether Link

Context
In your environment the database layer is integrated in another repository. This guide explains the DB artifacts the backend expects, migration steps, and integration tips so the separate DB repo can host schema and migrations.

Expected models (minimal)
- `users` table: id (pk), email (unique), username, hashed_password, full_name, role, is_active, is_verified, last_login, created_at, updated_at
- `courses` table: id, title, slug, teacher_id, status, price, description, total_sessions, created_at, updated_at
- `sessions` table: id, course_id, session_number, title, date_time, duration_minutes, zoom_meeting_id, zoom_join_url, zoom_start_url, zoom_password, recording_url, recording_available, created_at, updated_at
- `refresh_tokens` table: id (pk), user_id (fk users.id), token_hash (sha256), created_at, expires_at, revoked (bool), replaced_by_id (fk refresh_tokens.id), ip_address, user_agent

Example SQL for `refresh_tokens` table

CREATE TABLE refresh_tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(128) NOT NULL UNIQUE,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
  expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  revoked BOOLEAN DEFAULT FALSE NOT NULL,
  replaced_by_id INTEGER REFERENCES refresh_tokens(id),
  ip_address VARCHAR(100),
  user_agent VARCHAR(255)
);
CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id);

Migration guidance (Alembic)
- Create an alembic revision that adds the `refresh_tokens` model. Example migration stub lives in `docs/` (you can adapt to your DB repo).
- Run migrations in staging before deploying to production.

Token hashing
- Backend stores SHA-256 hash of the raw opaque token. The raw token is returned to client only once. When the client presents the token, backend hashes and compares.

Retention policy and cleanup
- Recommended: TTL for refresh tokens (e.g., 7-30 days). Periodically cleanup expired tokens with a scheduled job.
- On detected token reuse, mark all user's tokens revoked and notify admins.

Integration tips
- If DB lives in a separate repo, expose repository interfaces that the backend imports (e.g., `UserRepository`, `RefreshTokenRepository`) or implement the Protocols defined in `app/core/backend_logic.py`.
- Expose health check endpoints and connection info to orchestrator.

Backups & security
- Ensure DB backups and encrypted storage for backups.
- Rotate DB credentials via secret manager and avoid hardcoding credentials in code.

