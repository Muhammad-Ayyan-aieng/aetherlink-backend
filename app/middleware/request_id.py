# ============================================================
# AETHER LINK - REQUEST ID MIDDLEWARE
# ============================================================

import time
import random
import string
import re
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Header names
REQUEST_ID_HEADER = "X-Request-ID"
FORWARDED_HEADER = "X-Forwarded-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate unique request IDs.
    
    Features:
    - Generates unique ID for each request
    - Accepts forwarded ID from client (if valid)
    - Stores in request.state.request_id
    - Adds X-Request-ID to response headers
    
    Usage:
        app.add_middleware(RequestIDMiddleware)
        
        # In other middleware/endpoints:
        request_id = request.state.request_id
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Generate or forward request ID.
        """
        # Check if client forwarded an ID
        forwarded_id = request.headers.get(FORWARDED_HEADER)
        
        if forwarded_id and self._is_valid_id(forwarded_id):
            request_id = forwarded_id
        else:
            # Generate new ID
            request_id = self._generate_request_id()
        
        # Store in request state for other middleware
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add ID to response headers
        response.headers[REQUEST_ID_HEADER] = request_id
        
        return response
    
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID.
        
        Format: {timestamp_ms}-{random_4chars}
        Example: 1704123456789-a7b3
        """
        timestamp = int(time.time() * 1000)
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{timestamp}-{random_chars}"
    
    def _is_valid_id(self, request_id: str) -> bool:
        """
        Validate forwarded request ID format.
        
        Valid format: timestamp-random
        Example: 1704123456789-a7b3
        """
        if not request_id or not isinstance(request_id, str):
            return False
        
        # Check length
        if len(request_id) < 10 or len(request_id) > 50:
            return False
        
        # Check format: digits-hyphen-alphanumeric
        if not re.match(r'^[0-9]+-[a-zA-Z0-9]+$', request_id):
            return False
        
        return True