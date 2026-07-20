Security Checklist — Aether Link

This checklist summarizes security considerations and mitigations to verify before production deployment.

Configuration
- [ ] `ALLOWED_ORIGINS` must list production frontend domains only (no `*`).
- [ ] `JWT_SECRET_KEY` must be strong and rotated securely.
- [ ] `ZOOM_WEBHOOK_SECRET` must be set; webhook endpoint rejects unsigned requests.

Authentication & Tokens
- [ ] Access tokens short-lived (1 hour) and signed (JWT).
- [ ] Refresh tokens opaque, stored server-side, rotated on refresh, and revocable.
- [ ] Store refresh tokens in httpOnly, Secure cookies where possible.

Rate limiting & Abuse
- [ ] Apply Redis-backed rate-limiter globally; enforce webhook rate limits.
- [ ] Ensure endpoints that accept large payloads (file upload, application) have stricter limits.

Data exposure
- [ ] Audit endpoints for exposure of `zoom_join_url`, `zoom_password`, `recording_url` and redact for public responses.
- [ ] Signed file URLs should be short-lived and only issued to authorized users.

File uploads
- [ ] Validate MIME type server-side (content sniffing), limit file size, and scan for malware.
- [ ] Store files in an object store (S3/GCS) rather than storing base64 in DB.

Webhooks
- [ ] Verify HMAC signature and optional timestamp/nonce for replay protection.
- [ ] Rate-limit webhook endpoints.

Logging & Auditing
- [ ] Add structured audit logs for login, refresh, revoke, payment verification, Zoom meeting creation/deletion.
- [ ] Avoid logging sensitive tokens or full request bodies in production logs.

Monitoring
- [ ] Health checks for DB and Redis and alerting on failures.
- [ ] Monitor for unusual token reuse patterns and failed login spikes.

Testing
- [ ] Unit tests for token rotation and reuse detection.
- [ ] Integration tests for webhook verification and Zoom interactions.

Operational
- [ ] Run database migrations in staging and verify schema compatibility with the DB repo.
- [ ] Use secret manager for credentials (Zoom, DB, JWT secret).

