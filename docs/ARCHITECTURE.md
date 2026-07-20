# Aether Link Architecture

## Purpose

This document describes the full backend architecture for Aether Link, including directory responsibilities, service layers, security patterns, data flows, and integration guidance.

## System Overview

Aether Link is a FastAPI backend for an online learning platform. It uses:
- FastAPI for HTTP APIs and middleware
- SQLAlchemy for ORM and database access
- Pydantic for request/response validation
- JWT access tokens and opaque refresh tokens for authentication
- Redis for caching and rate limiting
- Zoom integration for live sessions and webhook handling

## Repository Layout

### Root
- `alembic/` — database migration environment and migration scripts
- `app/` — application code
- `docs/` — documentation and architecture guides
- `requirements.txt` — Python dependency list
- `alembic.ini` — Alembic configuration

### `app/`
- `api/v1/` — FastAPI routers grouped by domain
- `core/` — app-wide configuration, database, security, Redis, and Zoom helpers
- `middleware/` — request/response middleware for logging, rate limiting, request IDs, and security headers
- `models/` — SQLAlchemy model definitions and enums
- `repositories/` — repository layer encapsulating database operations
- `schemas/` — Pydantic request/response schemas
- `services/` — business logic and orchestration layer
- `utils/` — reusable helper code
- `main.py` — FastAPI app factory and lifespan startup/shutdown logic

## Layered Architecture

### API Layer

`app/api/v1/router.py` aggregates all route modules and exposes the `/api/v1` API surface.

Each module in `app/api/v1/` follows a pattern:
- define routes and HTTP metadata
- validate input/response with Pydantic schemas from `app/schemas/`
- enforce auth and roles using dependencies from `app/core/dependencies.py`
- call services implemented in `app/services/`
- return structured response or raise FastAPI HTTP exceptions

Key route modules:
- `auth.py` — login, refresh, logout, revoke
- `users.py` — profile, profile updates, admin user management
- `courses.py` — course CRUD and public listing
- `sessions.py` — session scheduling, Zoom meeting management, public session views
- `enrollments.py` — student enrollments and admin verification
- `attendance.py` — attendance tracking and admin reports
- `materials.py` — course material upload/download and authorization
- `payments.py` — payment lifecycle, verification, refunds
- `invitations.py` — teacher invitation flow
- `applications.py` — public application submission and admin review
- `admin.py` — admin dashboard endpoints and reports
- `webhooks.py` — incoming Zoom webhook receiver

### Core Layer

`app/core/` contains reusable infrastructure and configuration.

- `config.py` — environment-driven settings with validation
- `database.py` — SQLAlchemy engine, session factory, `get_db` dependency, connection testing
- `dependencies.py` — authentication and role enforcement dependencies, rate limiter prototypes
- `security.py` — token encode/decode, password hashing, token extraction
- `redis.py` — Redis client wrapper used for caching/rate limiting
- `zoom.py` — Zoom API and webhook utilities
- `email.py` — email sending helper wrappers
- `supabase.py` — storage helpers for course materials

### Middleware

`app/middleware/` contains cross-cutting HTTP middleware:
- `request_id.py` — generates and attaches a unique request ID
- `logging.py` — structured request/response logging
- `rate_limit.py` — centralized rate limiting enforcement
- `security.py` — security headers, CSP, CORS enforcement
- `rate_limit_backup.py` — fallback rate limiting logic

Middleware order in `app/main.py` is intentional:
1. Request ID
2. Logging
3. Rate limiting
4. Security headers
5. CORS

### Models Layer

`app/models/` defines the database domain model.
- `user.py` — users, roles, status fields
- `course.py` — course metadata and teacher relation
- `sessions.py` — class sessions, Zoom meeting fields, status
- `enrollment.py` — enrollment status and payment method
- `attendance.py` — attendance records and status
- `material.py` — course materials and storage metadata
- `payments.py` — payment records and statuses
- `application.py` — public applications from students or visitors
- `invitations.py` — teacher invitation tokens and status
- `refresh_token.py` — opaque refresh token storage and revocation

### Repositories Layer

`app/repositories/` is the persistence abstraction.
- each repository encapsulates query logic for one model
- services call repositories instead of direct ORM queries
- this separates business rules from persistence details and enables future DB portability

Examples:
- `user_repository.py` — user lookup, create, update operations
- `session_repository.py` — session retrieval and Zoom metadata updates
- `refresh_token_repository.py` — store/lookup/revoke hashed refresh tokens

### Services Layer

`app/services/` contains business workflows and orchestrates domain actions.
- `auth_service.py` — JWT issuance, refresh token rotation, logout, revoke, account activation
- `course_service.py` — course creation, updates, publish workflows
- `session_service.py` — schedule sessions, Zoom meeting creation, public session redaction
- `zoom_service.py` — Zoom meeting API operations and webhook handling
- `payment_service.py` — payment verification and refund workflows
- `invitation_service.py` — send/resend teacher invitations and accept flows
- `attendance_service.py` — attendance marking and reporting
- `material_service.py` — file upload validation and signed URL generation

Services are intentionally stateless and injected with a DB session or repository instance.

### Schemas Layer

`app/schemas/` defines Pydantic models for:
- request validation
- response serialization
- payload contracts between frontend and backend

This prevents raw dicts from being processed without validation and helps document the API automatically.

### Utilities

`app/utils/` contains shared helpers:
- `date_utils.py` — date parsing and formatting helpers
- `email.py` — email templates and sanitization
- `file_utils.py` — file size/type validation and base64 helpers
- `helpers.py` — generic helper functions used across the app
- `response_utils.py` — response shaping helpers
- `sanitizer.py` — input sanitization utilities
- `slug_generator.py` — SEO-friendly slug generation
- `validator.py` / `validators.py` — custom validators and rule enforcement

## Request Lifecycle

1. Client sends HTTP request to `/api/v1/...`
2. FastAPI router matches the handler in `app/api/v1/*`
3. Dependencies execute:
   - `get_db()` opens a DB session
   - auth dependency validates JWT and loads current user
   - role dependencies enforce admin/teacher/student access
   - rate limiter applies request quotas
4. Route handler validates request payload with Pydantic schema
5. Handler calls a service in `app/services/`
6. Service uses repositories in `app/repositories/` to read/write data
7. Database session commits on success and closes after request
8. Response is serialized back to JSON

## Authentication & Authorization

Auth is handled using:
- `OAuth2PasswordBearer` for access token extraction
- short-lived JWT access tokens
- opaque refresh tokens stored hashed in the database
- role-based dependencies in `app/core/dependencies.py`

Roles supported:
- `ADMIN`
- `TEACHER`
- `STUDENT`

Common auth dependencies:
- `get_current_user`
- `get_current_active_user`
- `get_current_verified_user`
- `get_current_admin_user`
- `get_current_teacher_user`
- `get_current_teacher_only`

## Zoom Integration

Zoom-related architecture spans:
- `app/core/zoom.py` — Zoom API helpers and webhook signature verification
- `app/services/zoom_service.py` — meeting creation and meeting hardening
- `app/api/v1/webhooks.py` — webhook receiver and event handling

Security hardening includes:
- verifying Zoom webhook HMAC signatures
- enforcing login requirements for meetings
- generating meeting passwords
- redacting Zoom join/start URLs from public session responses

## Database & Migrations

The database layer is SQLAlchemy with a separate Alembic migration setup.

`app/core/database.py` provides:
- engine creation
- session factory
- `get_db` dependency
- connection test and debug utilities

`alembic/` provides migration infrastructure; `docs/database/DATABASE_INTEGRATION.md` describes expected DB artifacts and refresh token schema.

## Security Patterns

Important security controls:
- role-based access control in route dependencies
- centralized request logging and error handling in `app/main.py`
- CORS configured with `settings.ALLOWED_ORIGINS`
- rate limiting middleware plus per-route rate limiting dependencies
- file upload validation using allowed extensions and MIME types
- secret storage through environment variables with `pydantic-settings`

## Deployment & Configuration

`app/core/config.py` defines environment-driven settings.
Key variables:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ZOOM_WEBHOOK_SECRET`
- `ALLOWED_ORIGINS`
- `REDIS_URL`
- `SUPABASE_URL` / `SUPABASE_SERVICE_KEY`

The app startup lifecycle in `app/main.py`:
- tests DB connection
- creates missing tables via SQLAlchemy metadata
- connects to Redis
- registers middleware and exception handlers

## Frontend Integration

The frontend contract is documented in `docs/frontend/FRONTEND_INSTRUCTIONS.md`.
Key integration points:
- login and refresh token flow
- secure storage of tokens (memory + httpOnly cookie)
- error handling for 401/refresh failures
- protected access to Zoom session URLs and course materials

## Best Practices for Extending the Project

When adding a new domain or feature, follow this architecture:
1. add model in `app/models/`
2. add schema(s) in `app/schemas/`
3. add persistence methods in `app/repositories/`
4. add business flow in `app/services/`
5. add API routes in `app/api/v1/`
6. add tests and update docs in `docs/`

## Notes on Directory Responsibilities

- `app/api/v1/`: HTTP surface and validation
- `app/services/`: business rules and orchestration
- `app/repositories/`: data access and queries
- `app/models/`: database schema and domain definitions
- `app/schemas/`: API contracts
- `app/core/`: shared platform infrastructure
- `app/middleware/`: request-level cross-cutting concerns
- `app/utils/`: reusable helpers and validation
- `docs/`: architecture, integration, and operational guidance

## Recommended Next Documentation Steps

- add `docs/FRONTEND_API_SPEC.md` with endpoint payload shapes
- add `docs/SECURITY.md` with threat model and mitigation details
- add `docs/OPERATIONS.md` for deployment, backup, and monitoring guidance
