# ============================================================
# AETHER LINK - RATE LIMIT MIDDLEWARE
# ============================================================

import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config import settings

# Rate limit configurations per endpoint type
RATE_LIMITS = {
    'default': {'requests': 100, 'period': 60},      # 100/min
    'auth': {'requests': 10, 'period': 60},          # 10/min (login, register)
    'admin': {'requests': 30, 'period': 60},         # 30/min
    'sensitive': {'requests': 5, 'period': 60},      # 5/min (password reset, etc.)
}

# Skip rate limiting for these paths
SKIP_PATHS = {
    '/health',
    '/health/detailed',
    '/docs',
    '/redoc',
    '/openapi.json',
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to rate limit requests per IP.
    
    Features:
    - Different limits for different endpoints
    - IP-based tracking (supports proxies)
    - Auto-cleanup of old entries
    - Rate limit headers in responses
    - Returns 429 when limit exceeded
    
    Usage:
        app.add_middleware(RateLimitMiddleware)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Store: {client_id: (count, reset_time)}
        self._cache: Dict[str, Tuple[int, float]] = {}
        
        # Max cache size (prevent memory exhaustion)
        self._max_cache_size = 10000
        
        # Cleanup counter
        self._cleanup_counter = 0
    
    async def dispatch(self, request: Request, call_next):
        """
        Check rate limit before processing request.
        """
        # Skip rate limiting for certain paths
        if request.url.path in SKIP_PATHS:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit for this endpoint
        limit_config = self._get_rate_limit(request)
        
        # Check if client is rate limited
        is_allowed, remaining, reset_time = self._check_rate_limit(
            client_id, 
            limit_config['requests'], 
            limit_config['period']
        )
        
        if not is_allowed:
            # Rate limit exceeded - Return 429 directly (avoid HTTPException)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": 429,
                        "message": f"Rate limit exceeded. Maximum {limit_config['requests']} requests per {limit_config['period']} seconds.",
                        "reset_at": reset_time,
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit_config['requests']),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time())),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit_config['requests'])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier (IP address).
        Supports proxies.
        """
        # Check X-Forwarded-For first (for proxies)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check X-Real-IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else 'unknown'
    
    def _get_rate_limit(self, request: Request) -> Dict[str, int]:
        """
        Get rate limit configuration for endpoint.
        """
        path = request.url.path.lower()
        
        # Auth endpoints (login, register)
        if '/auth/' in path:
            return RATE_LIMITS['auth']
        
        # Admin endpoints
        if '/admin/' in path:
            return RATE_LIMITS['admin']
        
        # Sensitive endpoints (password reset, etc.)
        if '/password' in path or '/reset' in path:
            return RATE_LIMITS['sensitive']
        
        # Default
        return RATE_LIMITS['default']
    
    def _check_rate_limit(
        self, 
        client_id: str, 
        max_requests: int, 
        period: int
    ) -> Tuple[bool, int, float]:
        """
        Check if client is rate limited.
        
        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        current_time = time.time()
        
        # Cleanup cache if too large
        if len(self._cache) > self._max_cache_size:
            self._cleanup_cache()
        
        # Get existing data or create new
        if client_id in self._cache:
            count, reset_time = self._cache[client_id]
        else:
            count = 0
            reset_time = current_time + period
        
        # Reset if period expired
        if current_time > reset_time:
            count = 0
            reset_time = current_time + period
        
        # Increment count
        count += 1
        self._cache[client_id] = (count, reset_time)
        
        # Check if limit exceeded
        if count > max_requests:
            remaining = 0
            return False, remaining, reset_time
        
        remaining = max_requests - count
        return True, remaining, reset_time
    
    def _cleanup_cache(self):
        """
        Remove expired entries from cache.
        """
        current_time = time.time()
        expired_keys = [
            client_id for client_id, (_, reset_time) in self._cache.items()
            if current_time > reset_time
        ]
        
        for client_id in expired_keys:
            del self._cache[client_id]
        
        # If still too large, remove oldest entries
        if len(self._cache) > self._max_cache_size:
            # Sort by reset_time (oldest first)
            sorted_items = sorted(
                self._cache.items(), 
                key=lambda x: x[1][1]
            )
            # Keep only first 80% of max size
            keep_count = int(self._max_cache_size * 0.8)
            for client_id, _ in sorted_items[keep_count:]:
                del self._cache[client_id]