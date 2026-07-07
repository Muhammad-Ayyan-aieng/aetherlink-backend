# ============================================================
# AETHER LINK - SESSIONS API
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Any
import logging
import traceback

from ...core.database import get_db
from ...core.dependencies import (
    get_current_user,
    get_current_teacher_user,
    get_current_admin_user,
    rate_limiter,
)
from ...core.config import settings
from ...services.session_service import SessionService
from ...services.course_service import CourseService
from ...services.zoom_service import ZoomService
from ...schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    RecordingAdd,
    SessionListResponse,
)
from ...models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# ============================================================
# COURSE SESSIONS (Public)
# ============================================================

@router.get(
    "/course/{course_id}",
    response_model=SessionListResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get course sessions",
    description="Get all sessions for a course.",
)
def get_course_sessions(
    course_id: int,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results limit (max 100)"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get sessions for a course.
    
    - **course_id**: Course ID
    - **skip**: Pagination offset
    - **limit**: Max results (1-100)
    """
    try:
        session_service = SessionService(db)
        result = session_service.get_sessions_by_course(
            course_id=course_id,
            skip=skip,
            limit=limit,
        )
        
        return {
            "sessions": result["sessions"],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# SESSION CRUD
# ============================================================

@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Get session by ID",
    description="Get session details.",
)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a session by ID.
    
    - **session_id**: Session ID
    """
    try:
        session_service = SessionService(db)
        session = session_service.get_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Create a session",
    description="Create a new session with Zoom meeting (teacher or admin only).",
)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new session with automatic Zoom meeting creation.
    
    **Teacher or Admin only.**
    
    - **course_id**: Course ID
    - **session_number**: Unique per course
    - **title**: 3-255 characters
    - **date_time**: Scheduled date and time
    - **duration_minutes**: 1-180 minutes
    - **description**: Optional description
    """
    try:
        session_service = SessionService(db)
        
        # Create session first
        session = session_service.create_session(
            session_data=session_data,
            user_id=current_user.id,
        )
        
        # Try to create Zoom meeting (don't fail if it doesn't work)
        try:
            # Check if Zoom credentials are configured
            if settings.ZOOM_ACCOUNT_ID and settings.ZOOM_CLIENT_ID and settings.ZOOM_CLIENT_SECRET:
                zoom_service = ZoomService(db)
                meeting_result = await zoom_service.create_meeting_for_session(
                    session_id=session.id,
                    topic=session_data.title,
                    start_time=session_data.date_time,
                    duration=session_data.duration_minutes or 60,
                    description=session_data.description,
                )
                logger.info(f"✅ Zoom meeting created for session {session.id}: {meeting_result.get('meeting_id')}")
                db.refresh(session)
            else:
                logger.warning("⚠️ Zoom credentials not configured, skipping Zoom meeting creation")
                
        except ImportError as e:
            logger.warning(f"⚠️ Zoom service not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create Zoom meeting: {e}")
            # Don't fail the session creation
        
        return session
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error creating session: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
    dependencies=[Depends(rate_limiter)],
    summary="Update a session",
    description="Update an existing session (teacher or admin only).",
)
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Update an existing session.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    - **title**: 3-255 characters
    - **date_time**: Scheduled date and time
    - **duration_minutes**: 1-180 minutes
    """
    try:
        session_service = SessionService(db)
        session = session_service.update_session(
            session_id=session_id,
            update_data=session_data,
            user_id=current_user.id,
        )
        
        # Update Zoom meeting if session has a Zoom meeting ID
        if session.zoom_meeting_id:
            try:
                zoom_service = ZoomService(db)
                await zoom_service.zoom_client.update_meeting(
                    meeting_id=session.zoom_meeting_id,
                    topic=session_data.title,
                    start_time=session_data.date_time,
                    duration=session_data.duration_minutes,
                    agenda=session_data.description,
                )
                logger.info(f"✅ Zoom meeting updated for session {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to update Zoom meeting: {e}")
        
        return session
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limiter)],
    summary="Delete a session",
    description="Delete a session and cancel Zoom meeting (teacher or admin only).",
)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a session and cancel Zoom meeting.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        session_service = SessionService(db)
        
        # Get session to check for Zoom meeting
        session = session_service.get_session(session_id)
        
        # Delete Zoom meeting if exists
        if session.zoom_meeting_id:
            try:
                zoom_service = ZoomService(db)
                await zoom_service.zoom_client.delete_meeting(session.zoom_meeting_id)
                logger.info(f"✅ Zoom meeting deleted for session {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete Zoom meeting: {e}")
        
        session_service.delete_session(
            session_id=session_id,
            user_id=current_user.id,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# ZOOM MEETING MANAGEMENT
# ============================================================

@router.post(
    "/{session_id}/zoom/create",
    response_model=SessionResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Create Zoom meeting",
    description="Create or recreate Zoom meeting for a session (teacher or admin only).",
)
async def create_zoom_meeting(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create or recreate Zoom meeting for a session.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        # Check if Zoom credentials are configured
        if not settings.ZOOM_ACCOUNT_ID or not settings.ZOOM_CLIENT_ID or not settings.ZOOM_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Zoom credentials not configured",
            )
        
        session_service = SessionService(db)
        session = session_service.get_session(session_id)
        
        # Use session object attributes directly (not .get())
        zoom_service = ZoomService(db)
        meeting_result = await zoom_service.create_meeting_for_session(
            session_id=session_id,
            topic=session.title,
            start_time=session.date_time,
            duration=session.duration_minutes or 60,
            description=session.description,
        )
        
        db.refresh(session)
        return session_service.get_session(session_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error creating Zoom meeting: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Zoom meeting: {str(e)}",
        )


@router.post(
    "/{session_id}/zoom/sync-attendance",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Sync Zoom attendance",
    description="Sync attendance from Zoom participants (teacher or admin only).",
)
async def sync_zoom_attendance(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync attendance from Zoom participants.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        zoom_service = ZoomService(db)
        result = await zoom_service.sync_attendance(session_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error syncing Zoom attendance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Zoom attendance: {str(e)}",
        )


@router.post(
    "/{session_id}/zoom/sync-recordings",
    dependencies=[Depends(get_current_teacher_user)],
    summary="Sync Zoom recordings",
    description="Sync recording URLs from Zoom (teacher or admin only).",
)
async def sync_zoom_recordings(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Sync recording URLs from Zoom.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        zoom_service = ZoomService(db)
        recordings = await zoom_service.sync_recordings(session_id)
        return {
            "session_id": session_id,
            "recordings": recordings,
            "count": len(recordings),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error syncing Zoom recordings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync Zoom recordings: {str(e)}",
        )


# ============================================================
# RECORDING MANAGEMENT
# ============================================================

@router.post(
    "/{session_id}/recording",
    response_model=SessionResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Add recording to session",
    description="Add recording URL to a session (teacher or admin only).",
)
def add_recording(
    session_id: int,
    recording_data: RecordingAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Add recording URL to a session.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    - **recording_url**: Valid URL
    """
    try:
        session_service = SessionService(db)
        session = session_service.add_recording(
            session_id=session_id,
            recording_url=recording_data.recording_url,
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# SESSION STATUS
# ============================================================

@router.put(
    "/{session_id}/complete",
    response_model=SessionResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Mark session as completed",
    description="Mark a session as completed (teacher or admin only).",
)
def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark session as completed.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        session_service = SessionService(db)
        session = session_service.mark_completed(
            session_id=session_id,
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{session_id}/cancel",
    response_model=SessionResponse,
    dependencies=[Depends(get_current_teacher_user)],
    summary="Cancel a session",
    description="Cancel a session (teacher or admin only).",
)
def cancel_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Cancel a session.
    
    **Teacher or Admin only.**
    
    - **session_id**: Session ID
    """
    try:
        session_service = SessionService(db)
        session = session_service.mark_cancelled(
            session_id=session_id,
            user_id=current_user.id,
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# UPCOMING SESSIONS
# ============================================================

@router.get(
    "/upcoming",
    response_model=List[SessionResponse],
    dependencies=[Depends(rate_limiter)],
    summary="Get upcoming sessions",
    description="Get upcoming sessions for the current user.",
)
def get_upcoming_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get upcoming sessions for the current student.
    
    **Requires authentication.**
    """
    try:
        session_service = SessionService(db)
        
        if current_user.role == UserRole.STUDENT:
            sessions = session_service.get_student_upcoming_sessions(current_user.id)
            return sessions
        elif current_user.role == UserRole.TEACHER:
            sessions = session_service.get_teacher_upcoming_sessions(current_user.id)
            return sessions
        else:
            # Admin - get all upcoming
            sessions = session_service.get_upcoming_sessions()
            return sessions
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/teacher/upcoming",
    response_model=List[SessionResponse],
    dependencies=[Depends(get_current_teacher_user)],
    summary="Get teacher's upcoming sessions",
    description="Get upcoming sessions for the current teacher.",
)
def get_teacher_upcoming(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get upcoming sessions for the current teacher.
    
    **Teacher only.**
    """
    try:
        session_service = SessionService(db)
        sessions = session_service.get_teacher_upcoming_sessions(current_user.id)
        return sessions
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )