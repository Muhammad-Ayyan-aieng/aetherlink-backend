# ============================================================
# AETHER LINK - ZOOM API CLIENT
# ============================================================

import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from ..core.config import settings

logger = logging.getLogger(__name__)


class ZoomClient:
    """Zoom API client for managing meetings, participants, and recordings."""

    def __init__(self):
        self.account_id = settings.ZOOM_ACCOUNT_ID
        self.client_id = settings.ZOOM_CLIENT_ID
        self.client_secret = settings.ZOOM_CLIENT_SECRET
        self.base_url = "https://api.zoom.us/v2"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def clear_token_cache(self):
        """Force token refresh on next request."""
        self._access_token = None
        self._token_expires_at = None
        logger.info("🔄 Zoom token cache cleared")

    async def _get_access_token(self) -> str:
        """
        Get OAuth access token using Server-to-Server OAuth.
        
        Returns:
            Access token string
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Check if token is still valid (with 5 min buffer)
        if self._access_token and self._token_expires_at:
            if datetime.now(timezone.utc) < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        if not all([self.account_id, self.client_id, self.client_secret]):
            logger.warning("Zoom credentials not configured")
            return ""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://zoom.us/oauth/token",
                    data={
                        "grant_type": "account_credentials",
                        "account_id": self.account_id,
                    },
                    auth=(self.client_id, self.client_secret),
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                logger.info("✅ Zoom access token obtained")
                return self._access_token
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Zoom token error: {e.response.status_code}")
            raise ValueError(f"Zoom authentication failed: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Zoom token error: {e}")
            raise ValueError(f"Zoom authentication failed: {str(e)}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Zoom API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/users/me/meetings")
            data: Request body
            params: Query parameters
            
        Returns:
            Response JSON
            
        Raises:
            ValueError: If request fails
        """
        token = await self._get_access_token()
        
        if not token:
            raise ValueError("Zoom credentials not configured")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    # Token expired, retry once
                    self._access_token = None
                    token = await self._get_access_token()
                    headers["Authorization"] = f"Bearer {token}"
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=data,
                        params=params,
                        timeout=30.0
                    )
                
                response.raise_for_status()
                
                if response.status_code == 204:
                    return {}
                    
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Zoom API error: {e.response.status_code}")
            if e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please try again later.")
            raise ValueError(f"Zoom API error: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Zoom API error: {e}")
            raise ValueError(f"Zoom API error: {str(e)}")

    # ============================================================
    # MEETING OPERATIONS
    # ============================================================

    async def create_meeting(
        self,
        topic: str,
        start_time: datetime,
        duration: int,
        agenda: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Zoom meeting.
        
        Args:
            topic: Meeting topic
            start_time: Meeting start time
            duration: Meeting duration in minutes
            agenda: Meeting agenda/description
            password: Meeting password (optional)
            
        Returns:
            Meeting details with id, join_url, start_url
        """
        data = {
            "topic": topic[:200],  # Zoom limit: 200 chars
            "type": 2,  # Scheduled meeting
            "start_time": start_time.isoformat(),
            "duration": duration,
            "timezone": "UTC",
            "agenda": agenda[:500] if agenda else "",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": True,
                "watermark": False,
                "use_pmi": False,
                "approval_type": 0,
                "audio": "both",
                "auto_recording": "cloud" if settings.ENVIRONMENT == "production" else "local",
                "enforce_login": False,
            }
        }

        if password:
            data["password"] = password

        response = await self._request("POST", "/users/me/meetings", data=data)
        
        return {
            "meeting_id": response.get("id"),
            "join_url": response.get("join_url"),
            "start_url": response.get("start_url"),
            "password": response.get("password"),
            "created_at": response.get("created_at"),
            "duration": response.get("duration"),
            "topic": response.get("topic"),
        }

    async def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get meeting details.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Meeting details
        """
        response = await self._request("GET", f"/meetings/{meeting_id}")
        
        return {
            "meeting_id": response.get("id"),
            "topic": response.get("topic"),
            "start_time": response.get("start_time"),
            "duration": response.get("duration"),
            "join_url": response.get("join_url"),
            "start_url": response.get("start_url"),
            "password": response.get("password"),
            "status": response.get("status"),
            "agenda": response.get("agenda"),
        }

    async def update_meeting(
        self,
        meeting_id: str,
        topic: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration: Optional[int] = None,
        agenda: Optional[str] = None
    ) -> bool:
        """
        Update a Zoom meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            topic: New topic
            start_time: New start time
            duration: New duration
            agenda: New agenda
            
        Returns:
            True if successful
        """
        data = {}
        if topic:
            data["topic"] = topic[:200]
        if start_time:
            data["start_time"] = start_time.isoformat()
        if duration:
            data["duration"] = duration
        if agenda:
            data["agenda"] = agenda[:500]

        if not data:
            return True

        await self._request("PATCH", f"/meetings/{meeting_id}", data=data)
        return True

    async def delete_meeting(self, meeting_id: str) -> bool:
        """
        Delete a Zoom meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            True if successful
        """
        await self._request("DELETE", f"/meetings/{meeting_id}")
        return True

    # ============================================================
    # PARTICIPANT OPERATIONS
    # ============================================================

    async def get_participants(
        self,
        meeting_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get participants from a meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            from_date: Start date for participants
            to_date: End date for participants
            
        Returns:
            List of participants
        """
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")

        response = await self._request(
            "GET",
            f"/past_meetings/{meeting_id}/participants",
            params=params
        )

        participants = response.get("participants", [])
        
        return [
            {
                "email": p.get("email", ""),
                "name": p.get("name", ""),
                "join_time": p.get("join_time"),
                "leave_time": p.get("leave_time"),
                "duration": p.get("duration"),
                "user_id": p.get("user_id"),
            }
            for p in participants
        ]

    async def get_participant_count(self, meeting_id: str) -> int:
        """
        Get participant count from a meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            Number of participants
        """
        params = {"page_size": 300}
        response = await self._request(
            "GET",
            f"/past_meetings/{meeting_id}/participants",
            params=params
        )
        return response.get("total_records", 0)

    # ============================================================
    # RECORDING OPERATIONS
    # ============================================================

    async def get_recordings(self, meeting_id: str) -> List[Dict[str, Any]]:
        """
        Get recordings for a meeting.
        
        Args:
            meeting_id: Zoom meeting ID
            
        Returns:
            List of recordings with URLs
        """
        try:
            response = await self._request(
                "GET",
                f"/meetings/{meeting_id}/recordings"
            )
            
            recordings = []
            for recording in response.get("recording_files", []):
                recordings.append({
                    "id": recording.get("id"),
                    "type": recording.get("recording_type"),
                    "url": recording.get("download_url"),
                    "play_url": recording.get("play_url"),
                    "file_size": recording.get("file_size"),
                    "file_type": recording.get("file_type"),
                    "status": recording.get("status"),
                })
            
            return recordings
            
        except ValueError as e:
            if "404" in str(e) or "not found" in str(e).lower():
                logger.info(f"No recordings found for meeting {meeting_id}")
                return []
            raise