# ============================================================
# AETHER LINK - LOGGING MIDDLEWARE
# ============================================================

import time
import logging
from typing import Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Skip logging for these paths (health checks, static files)
SKIP_PATHS: Set[str] = {
    '/health',
    '/health/detailed',
    '/docs',
    '/redoc',
    '/openapi.json',
}

# Sensitive headers to mask
SENSITIVE_HEADERS = {'authorization', 'cookie', 'x-api-key'}


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses.
    
    Features:
    - Logs request method, path, IP, user-agent
    - Logs response status and time
    - Skips health check endpoints
    - Masks sensitive headers
    - Logs slow requests as warnings
    
    Usage:
        app.add_middleware(LoggingMiddleware)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Log request and response with timing.
        """
        # Skip logging for certain paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)
        
        # Get request details
        request_id = getattr(request.state, 'request_id', 'unknown')
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', 'unknown')[:100]
        
        start_time = time.time()
        
        # Log request
        logger.info(
            f"📥 [{request_id}] {request.method} {request.url.path} "
            f"IP={client_ip} UA={user_agent}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000
        
        # Log response with status symbol
        if response.status_code < 400:
            status_symbol = "✅"
        elif response.status_code < 500:
            status_symbol = "⚠️"
        else:
            status_symbol = "❌"
        
        logger.info(
            f"{status_symbol} [{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({process_time:.2f}ms)"
        )
        
        # Log slow requests (>1s) as warning
        if process_time > 1000:
            logger.warning(
                f"🐢 [{request_id}] Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}ms"
            )
        
        # Log errors (5xx) as error
        if response.status_code >= 500:
            logger.error(
                f"💥 [{request_id}] Server error: {request.method} {request.url.path} "
                f"→ {response.status_code}"
            )
        
        # Add timing header
        response.headers["X-Response-Time-MS"] = f"{process_time:.2f}"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        Supports proxies (X-Forwarded-For).
        """
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else 'unknown'