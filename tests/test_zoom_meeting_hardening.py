import pytest
import asyncio
from app.core.backend_logic import create_session_logic


class DummySessionRepo:
    def create(self, payload):
        # emulate DB-created session
        s = dict(payload)
        s["id"] = 999
        return s


class DummyZoomClient:
    async def create_meeting(self, **kwargs):
        # return minimal meeting info and echo settings
        return {"meeting_id": "m-123", "password": kwargs.get("password", "pwd"), "settings": kwargs.get("settings", {})}


@pytest.mark.asyncio
async def test_create_session_with_zoom():
    session_payload = {"course_id": 1, "title": "Test", "date_time": "2026-07-14T10:00:00Z"}
    session_repo = DummySessionRepo()
    zoom_client = DummyZoomClient()

    def gen_meta(payload):
        return {"topic": payload.get("title"), "password": "auto-generated", "settings": {"enforce_login": True}}

    result = await create_session_logic(session_payload, session_repo, zoom_client=zoom_client, generate_meeting_meta=gen_meta)
    assert result.get("id") == 999
    assert result.get("zoom_meeting", {}).get("meeting_id") == "m-123"
    assert result.get("zoom_meeting", {}).get("settings", {}).get("enforce_login") is True
