Aether Link — Project Documentation

Overview

Aether Link is an online course management backend built with FastAPI, SQLAlchemy, and Pydantic. Key features:
- User accounts (students, teachers, admins)
- Course and session management with Zoom integration
- Enrollments, attendance tracking, materials and file uploads
- Payments and administrative workflows
- Webhook integrations (Zoom)
- JWT access tokens + opaque refresh token rotation (server-side)

Repository structure (important folders)
- app/api/v1/ — all route modules (auth, users, courses, sessions, enrollments, attendance, payments, materials, invitations, admin, webhooks, applications)
- app/services/ — business logic services (AuthService, SessionService, ZoomService, etc.)
- app/repositories/ — DB access layer (SQLAlchemy-based). In your setup DB code may live in another repo; services call repository interfaces.
- app/models/ — SQLAlchemy models (User, Course, Session, RefreshToken, ...)
- app/schemas/ — Pydantic schemas (request/response validation)
- app/core/ — configuration, database connection, Redis wrapper, Zoom helper
- app/middleware/ — logging, rate-limiting, security headers
- docs/ — project docs (this folder)

Endpoints summary
- Auth: /api/v1/auth (login, refresh, logout, revoke)
- Users: /api/v1/users (profile, admin user management)
- Courses: /api/v1/courses (public and teacher/admin operations)
- Sessions: /api/v1/sessions (public course sessions + protected session management)
- Enrollments: /api/v1/enrollments
- Attendance: /api/v1/attendance
- Materials: /api/v1/materials
- Payments: /api/v1/payments
- Invitations: /api/v1/invitations
- Applications: /api/v1/applications (public application submission)
- Webhooks: /api/v1/webhooks/zoom (Zoom webhook receiver)

Key design decisions
- Use JWT for short-lived access tokens (stateless) and opaque server-stored refresh tokens for rotation/revocation.
- Zoom integration: server manages meeting creation (with `enforce_login` + generated password) and webhooks for events.
- Redis is used for some caching and rate-limiting.

Known bugs and recommended fixes (action items)
1. Missing Alembic migration for `refresh_tokens` table. Create migration before deploying. (HIGH)
2. `users.update_profile_picture` uses `request.body()` without `await` and naive parsing — fix to `await request.body()` and robust validation. (BUG / HIGH)
3. `/webhooks/zoom` currently has no rate-limiter dependency — add to reduce abuse. (HIGH)
4. `settings.ALLOWED_ORIGINS` may include wildcard `*` — tighten origin list in production. (HIGH)
5. Duplicate rate-limiting: middleware + per-route dependency exist — consolidate to a single Redis-backed middleware. (MEDIUM)
6. Some endpoints accept raw dict payloads without Pydantic validation (e.g., `payments.refund`) — replace with request schemas. (MEDIUM)
7. File upload handling: base64-in-DB storage and lack of virus scanning. Add content sniffing and integrate virus scanning or storage in object store. (MEDIUM)
8. Error handling sometimes returns raw exceptions — standardize and avoid leaking stack traces. (LOW)
9. Audit logging for critical actions (token issuance/revocation, Zoom meeting creation/deletion, payment verification) is limited — add structured audit logs. (MEDIUM)
10. Sensitive fields: verify all endpoints that may leak `zoom_join_url`, `zoom_password`, or `recording_url`. Public responses must be redacted. (MEDIUM)

Security hardening done
- Zoom webhook HMAC verification added.
- Public session listing redacts Zoom join links and passwords.
- Meeting creation enforces Zoom sign-in and generates meeting passwords.
- Refresh tokens converted to opaque server-stored tokens and rotation implemented in `AuthService`.

Migration & deployment notes
- Add Alembic migration for `refresh_tokens` table. Example SQL provided in `docs/database/DATABASE_INTEGRATION.md`.
- Ensure `ZOOM_WEBHOOK_SECRET` is set in environment for webhook verification.
- Ensure `ALLOWED_ORIGINS` is set to production domains; do not use `*` with credentials.
- Run backend tests and integration tests against staging Zoom account before rolling out.

Testing guidance
- Unit tests for auth flow: login → refresh (rotation) → reuse detection.
- Integration tests for webhook verification (signed payloads) and Zoom meeting creation.
- Tests for file upload validation and material access authorization.

Next steps (recommended priorities)
1. Create and run Alembic migration for `refresh_tokens` table. (urgent)
2. Fix `users.update_profile_picture` bug and other input parsing issues. (urgent)
3. Add webhook rate-limiting and consolidate rate limiting. (high)
4. Add audit logging and admin token management endpoints. (high)
5. Add tests and CI jobs. (high)

Contact
- For help integrating the DB from another repo, follow `docs/database/DATABASE_INTEGRATION.md`.

