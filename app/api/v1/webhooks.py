# ============================================================
# AETHER LINK - WEBHOOKS
# ============================================================

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
import logging
import base64
import time

from ...core.database import get_db
from ...core.config import settings
from ...core.dependencies import rate_limiter
from ...services.zoom_service import ZoomService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/zoom", dependencies=[Depends(rate_limiter)])
async def zoom_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    """
    Zoom webhook endpoint for meeting events.
    
    Handles:
    - Meeting started/ended
    - Participant joined/left
    - Recording completed
    """
    # Verify webhook signature (if configured)
    raw_body = await request.body()

    if settings.ZOOM_WEBHOOK_SECRET:
        signature = request.headers.get("x-zm-signature")
        timestamp = request.headers.get("x-zm-request-timestamp")

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature"
            )

        # Optional replay protection: validate timestamp within allowed window
        try:
            if timestamp:
                req_ts = int(timestamp)
                now = int(time.time())
                if abs(now - req_ts) > 300:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Webhook timestamp outside allowed window"
                    )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook timestamp"
            )

        secret = settings.ZOOM_WEBHOOK_SECRET
        verified = False

        # Try a couple of common signing formats: HMAC over body, and HMAC over timestamp+body
        candidates = [raw_body]
        if timestamp:
            candidates.insert(0, timestamp.encode() + raw_body)

        header_val = signature
        if header_val.startswith("v0="):
            header_val = header_val[3:]

        for candidate in candidates:
            digest = hmac.new(secret.encode(), candidate, hashlib.sha256).digest()
            hex_sig = digest.hex()
            b64_sig = base64.b64encode(digest).decode()

            # Use constant-time compare
            if hmac.compare_digest(header_val, hex_sig) or hmac.compare_digest(header_val, b64_sig):
                verified = True
                break

        if not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    try:
        body = json.loads(raw_body) if raw_body else {}
        event = body.get("event")
        payload = body.get("payload", {})

        logger.info(f"📥 Zoom webhook received: {event}")

        if event == "meeting.started":
            await handle_meeting_started(payload, db)
        elif event == "meeting.ended":
            await handle_meeting_ended(payload, db)
        elif event == "recording.completed":
            await handle_recording_completed(payload, db)
        elif event == "meeting.participant_joined":
            await handle_participant_joined(payload, db)
        elif event == "meeting.participant_left":
            await handle_participant_left(payload, db)
        else:
            logger.info(f"Unhandled Zoom event: {event}")

        return {"status": "ok"}

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body"
        )
    except Exception as e:
        logger.error(f"❌ Zoom webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def handle_meeting_started(payload: dict, db: Session) -> None:
    """Handle meeting.started event."""
    meeting_id = payload.get("object", {}).get("id")
    if not meeting_id:
        return
    
    # Find session by zoom_meeting_id and update status
    from ...repositories.session_repository import SessionRepository
    session_repo = SessionRepository(db)
    
    # Update session status (you may want to add this logic)


async def handle_meeting_ended(payload: dict, db: Session) -> None:
    """Handle meeting.ended event."""
    meeting_id = payload.get("object", {}).get("id")
    if not meeting_id:
        return
    
    # Trigger attendance sync
    try:
        zoom_service = ZoomService(db)
        # Find session by zoom_meeting_id
        # For now, we'll log
        logger.info(f"Meeting {meeting_id} ended, syncing attendance...")
    except Exception as e:
        logger.error(f"Failed to sync attendance: {e}")


async def handle_recording_completed(payload: dict, db: Session) -> None:
    """Handle recording.completed event."""
    meeting_id = payload.get("object", {}).get("id")
    if not meeting_id:
        return
    
    # Sync recordings
    try:
        zoom_service = ZoomService(db)
        # Find session by zoom_meeting_id
        logger.info(f"Recording completed for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"Failed to sync recordings: {e}")


async def handle_participant_joined(payload: dict, db: Session) -> None:
    """Handle participant_joined event."""
    meeting_id = payload.get("object", {}).get("id")
    participant = payload.get("object", {}).get("participant", {})
    logger.info(f"Participant joined: {participant.get('user_name')} in meeting {meeting_id}")


async def handle_participant_left(payload: dict, db: Session) -> None:
    """Handle participant_left event."""
    meeting_id = payload.get("object", {}).get("id")
    participant = payload.get("object", {}).get("participant", {})
    logger.info(f"Participant left: {participant.get('user_name')} in meeting {meeting_id}")