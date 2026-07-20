import pytest
from datetime import datetime, timedelta
from app.core import backend_logic


class FakeUserRepo:
    def __init__(self):
        self.users = {1: {"id": 1, "email": "test@example.com", "hashed_password": "hashed", "is_active": True, "role": "student", "username": "testuser", "full_name": "Test User"}}
        self.last_login = None

    def get_by_email(self, email: str):
        return self.users.get(1) if email == "test@example.com" else None

    def get_by_id(self, user_id: int):
        return self.users.get(user_id)

    def update_last_login(self, user_id: int):
        self.last_login = datetime.utcnow()


class FakeRefreshRepo:
    def __init__(self):
        self.storage = {}

    def create(self, user_id: int, token_str: str, expires_at: datetime, meta=None):
        self.storage[token_str] = {"user_id": user_id, "token_str": token_str, "expires_at": expires_at, "revoked": False}
        return self.storage[token_str]

    def get_by_hash(self, token_str: str):
        return self.storage.get(token_str)

    def revoke(self, token_record):
        token_record["revoked"] = True

    def revoke_all_for_user(self, user_id: int):
        count = 0
        for t in self.storage.values():
            if t["user_id"] == user_id and not t["revoked"]:
                t["revoked"] = True
                count += 1
        return count

    def mark_replaced(self, old_token, new_token):
        old_token["revoked"] = True
        old_token["replaced_by"] = new_token["token_str"]


def fake_verify(password, hashed):
    return password == "correct" and hashed == "hashed"


def fake_create_access(payload):
    return "access.jwt.token"


def test_login_and_refresh_rotation():
    user_repo = FakeUserRepo()
    refresh_repo = FakeRefreshRepo()

    # Login
    result = backend_logic.login_logic(
        email="test@example.com",
        password="correct",
        user_repo=user_repo,
        verify_password_fn=fake_verify,
        create_access_token=fake_create_access,
        refresh_repo=refresh_repo,
        refresh_ttl_days=7,
    )

    assert "access_token" in result
    assert "refresh_token" in result
    first_refresh = result["refresh_token"]

    # Refresh
    res2 = backend_logic.refresh_logic(
        presented_refresh=first_refresh,
        refresh_repo=refresh_repo,
        user_repo=user_repo,
        create_access_token=fake_create_access,
        refresh_ttl_days=7,
    )

    assert "access_token" in res2
    assert "refresh_token" in res2
    assert res2["refresh_token"] != first_refresh

    # Using revoked token should revoke all
    with pytest.raises(ValueError):
        backend_logic.refresh_logic(
            presented_refresh=first_refresh,
            refresh_repo=refresh_repo,
            user_repo=user_repo,
            create_access_token=fake_create_access,
            refresh_ttl_days=7,
        )

    # Ensure all tokens revoked
    count = sum(1 for t in refresh_repo.storage.values() if t.get("revoked"))
    assert count >= 1
