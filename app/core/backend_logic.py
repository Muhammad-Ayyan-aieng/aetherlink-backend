"""
DB-agnostic backend logic functions.
These functions implement business rules and accept repository interfaces
(or protocol objects) rather than talking to the DB directly.

Keep this file free of any SQLAlchemy / DB session usage so it can be
used from another repo that provides concrete repository implementations.
"""
from typing import Protocol, Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
import secrets


# ---------------------------
# Protocols (interfaces)
# ---------------------------
class UserRepo(Protocol):
    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]: ...
    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]: ...
    def update_last_login(self, user_id: int) -> None: ...


class RefreshTokenRepo(Protocol):
    def create(self, user_id: int, token_str: str, expires_at: datetime, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def get_by_hash(self, token_str: str) -> Optional[Dict[str, Any]]: ...
    def revoke(self, token_record: Dict[str, Any]) -> None: ...
    def revoke_all_for_user(self, user_id: int) -> int: ...
    def mark_replaced(self, old_token: Dict[str, Any], new_token: Dict[str, Any]) -> None: ...


class SessionRepo(Protocol):
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def get_by_id(self, session_id: int) -> Optional[Dict[str, Any]]: ...
    def update(self, session_id: int, payload: Dict[str, Any]) -> Dict[str, Any]: ...


class ZoomClient(Protocol):
    async def create_meeting(self, **kwargs) -> Dict[str, Any]: ...
    async def update_meeting(self, meeting_id: str, **kwargs) -> Dict[str, Any]: ...
    async def delete_meeting(self, meeting_id: str) -> None: ...


# ---------------------------
# Token creation hook types
# ---------------------------
CreateAccessTokenFn = Callable[[Dict[str, Any]], str]


# ---------------------------
# Business logic functions
# ---------------------------

def login_logic(
    email: str,
    password: str,
    user_repo: UserRepo,
    verify_password_fn: Callable[[str, str], bool],
    create_access_token: CreateAccessTokenFn,
    refresh_repo: RefreshTokenRepo,
    refresh_ttl_days: int = 7,
) -> Dict[str, Any]:
    """Authenticate user and return access + opaque refresh token.

    - `user_repo` must return a dict with at least: id, email, hashed_password, is_active, role
    - `verify_password_fn(password, hashed)` returns True/False
    - `create_access_token` takes payload dict and returns JWT string
    """
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Invalid email")

    user = user_repo.get_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    if not user.get("is_active"):
        raise ValueError("Account inactive or pending approval")

    if not verify_password_fn(password, user.get("hashed_password")):
        raise ValueError("Invalid credentials")

    # update last login
    try:
        user_repo.update_last_login(user["id"])
    except Exception:
        pass

    # access token
    token_data = {"sub": str(user["id"]), "email": user["email"], "role": user.get("role")}
    access_token = create_access_token(token_data)

    # opaque refresh token
    refresh_token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=refresh_ttl_days)
    refresh_repo.create(user_id=user["id"], token_str=refresh_token, expires_at=expires_at, meta={})

    return {
        "user": {k: user.get(k) for k in ("id", "email", "username", "full_name", "role")},
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


def refresh_logic(
    presented_refresh: str,
    refresh_repo: RefreshTokenRepo,
    user_repo: UserRepo,
    create_access_token: CreateAccessTokenFn,
    refresh_ttl_days: int = 7,
) -> Dict[str, Any]:
    """Rotate refresh token and return new access+refresh tokens.

    - If a revoked token is presented, revoke all tokens for the user (suspected reuse).
    """
    record = refresh_repo.get_by_hash(presented_refresh)
    if not record:
        raise ValueError("Invalid refresh token")

    if record.get("revoked"):
        # token reuse detected
        refresh_repo.revoke_all_for_user(record["user_id"])
        raise ValueError("Refresh token revoked")

    if record.get("expires_at") and record["expires_at"] < datetime.utcnow():
        raise ValueError("Refresh token expired")

    user = user_repo.get_by_id(record["user_id"])
    if not user or not user.get("is_active"):
        raise ValueError("User not found or inactive")

    # rotate
    new_refresh = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(days=refresh_ttl_days)
    new_record = refresh_repo.create(user_id=user["id"], token_str=new_refresh, expires_at=expires_at, meta={})
    refresh_repo.mark_replaced(record, new_record)

    token_data = {"sub": str(user["id"]), "email": user["email"], "role": user.get("role")}
    new_access = create_access_token(token_data)

    return {"access_token": new_access, "refresh_token": new_refresh, "expires_in": 3600}


def revoke_refresh_logic(presented_refresh: str, refresh_repo: RefreshTokenRepo) -> Dict[str, Any]:
    rec = refresh_repo.get_by_hash(presented_refresh)
    if not rec:
        raise ValueError("Invalid refresh token")
    refresh_repo.revoke(rec)
    return {"message": "Refresh token revoked"}


async def create_session_logic(
    session_payload: Dict[str, Any],
    session_repo: SessionRepo,
    zoom_client: Optional[ZoomClient] = None,
    generate_meeting_meta: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create session record and optionally create a Zoom meeting via injected client.

    The `generate_meeting_meta` hook can be used to adapt meeting parameters.
    """
    # create session in upstream repo (DB handled by other repo)
    session = session_repo.create(session_payload)

    # create zoom meeting if client provided
    if zoom_client:
        try:
            meeting_kwargs = generate_meeting_meta(session_payload) if generate_meeting_meta else {}
            meeting_result = await zoom_client.create_meeting(**meeting_kwargs)
            # return combined result (caller should persist meeting IDs via its repo)
            session["zoom_meeting"] = meeting_result
        except Exception:
            # do not fail session creation if Zoom fails
            session["zoom_meeting_error"] = True

    # redact sensitive fields for any public-facing return
    safe = dict(session)
    for fld in ("zoom_join_url", "zoom_start_url", "zoom_password"):
        if fld in safe:
            safe[fld] = None

    return safe


def enroll_student_logic(student_id: int, course_id: int, enrollment_checker: Callable[[int, int], bool], enrollment_creator: Callable[..., Dict[str, Any]]) -> Dict[str, Any]:
    """Enroll a student if not already enrolled."""
    if not enrollment_checker(student_id, course_id):
        return enrollment_creator(student_id=student_id, course_id=course_id)
    raise ValueError("Already enrolled")


# Add other logic helpers as needed (material access, signing URLs, recording checks, etc.)

def redact_session_public(session_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Return a sanitized session dict safe for public listing."""
    s = dict(session_obj)
    for k in ("zoom_join_url", "zoom_start_url", "zoom_password", "recording_url"):
        s.pop(k, None)
    return s
