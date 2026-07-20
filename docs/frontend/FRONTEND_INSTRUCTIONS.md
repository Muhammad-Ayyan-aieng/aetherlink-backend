Frontend Integration Guide — Aether Link

Purpose
This document explains how the frontend should interact with the backend APIs, authentication model, and UX considerations for security-sensitive features.

Auth & Tokens
- Access token: JWT, short-lived (~1 hour). Include as `Authorization: Bearer <token>` header.
- Refresh token: opaque random string. The server rotates refresh tokens on `/auth/refresh` and stores them server-side.

Recommended storage
- Store the access token in memory (e.g., React context) or a short-lived store. Do not store the access token in localStorage if XSS is a risk.
- Store the refresh token in an `httpOnly`, `Secure` cookie scoped to the backend domain. If you cannot use cookies, store it in secure storage on mobile apps.
- On receiving a new refresh token from `/auth/refresh`, replace the stored token immediately.

Auth flows
- Login: POST `/api/v1/auth/login` with `{ email, password }`. Backend returns `access_token`, `refresh_token`, `user`.
- Refresh: POST `/api/v1/auth/refresh` with `{ refresh_token }` (or rely on cookie). Backend returns rotated `refresh_token` and new `access_token`.
- Logout: POST `/api/v1/auth/logout` and call `/auth/revoke-refresh` if you want to revoke server-side.

Handling 401s
- On 401 from an API call, call `/api/v1/auth/refresh`. If refresh succeeds, retry the original request once. If refresh fails, redirect to login.

UI considerations for Zoom and sensitive data
- Do not display `zoom_join_url`, `zoom_start_url`, `zoom_password` on public pages. Only fetch session details for authenticated and authorized users.
- For materials that are files, the backend returns signed short-lived URLs for authorized users — implement download via signed URL fetch.

File uploads
- Perform client-side checks: file type and max size. But rely on the server to enforce final validation.
- For image uploads, show a preview before uploading but do not allow arbitrary HTML insertion.

Forms & validation
- Use client-side validation to improve UX but always validate on server: length, types, and allowed enumerations.

Error handling & UX
- Map server error codes to friendly messages. For security-related codes like `ACCOUNT_INACTIVE` (403) show instructions to contact admin.
- Do not expose raw server error details to users.

Rate limits & retries
- Be conservative with retry logic. Respect `Retry-After` if returned. Avoid aggressive retry loops on rate-limited endpoints.

Testing the frontend
- Test auth flows including refresh rotation and reuse detection (simulate old refresh token reuse and ensure backend forces logout).
- Test Zoom flows by verifying that join URLs are only obtained when the user is authorized.

API spec reference
See `docs/FRONTEND_API_SPEC.md` for a concise endpoint list and payload shapes.

Deployment notes
- Ensure CORS configuration allows the frontend origin(s) and uses `Access-Control-Allow-Credentials: true` only when storing refresh token in cookies.

