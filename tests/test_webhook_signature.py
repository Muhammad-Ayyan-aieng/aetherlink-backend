import hmac
import hashlib
import base64
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


def compute_signature(secret: str, body: bytes, timestamp: str = None):
    candidates = [body]
    if timestamp:
        candidates.insert(0, timestamp.encode() + body)

    # Use hex digest for test header
    digest = hmac.new(secret.encode(), candidates[0], hashlib.sha256).digest()
    return digest.hex()


def test_zoom_webhook_signature_valid(monkeypatch):
    client = TestClient(app)

    # Ensure secret is set
    monkeypatch.setattr(settings, "ZOOM_WEBHOOK_SECRET", "testsecret")

    payload = {"event": "meeting.started", "payload": {"object": {"id": "12345"}}}
    body = json.dumps(payload).encode('utf-8')
    ts = str(int(__import__('time').time()))
    sig = compute_signature("testsecret", ts.encode() + body)

    headers = {
        "x-zm-signature": f"v0={sig}",
        "x-zm-request-timestamp": ts,
        "content-type": "application/json",
    }

    resp = client.post("/api/v1/webhooks/zoom", data=body, headers=headers)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_zoom_webhook_signature_invalid(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(settings, "ZOOM_WEBHOOK_SECRET", "testsecret")

    payload = {"event": "meeting.started", "payload": {"object": {"id": "12345"}}}
    body = json.dumps(payload).encode('utf-8')
    ts = str(int(__import__('time').time()))
    # wrong secret
    sig = compute_signature("wrong", ts.encode() + body)

    headers = {
        "x-zm-signature": f"v0={sig}",
        "x-zm-request-timestamp": ts,
        "content-type": "application/json",
    }

    resp = client.post("/api/v1/webhooks/zoom", data=body, headers=headers)
    assert resp.status_code == 401
