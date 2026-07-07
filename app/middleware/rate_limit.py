# ============================================================
# AETHER LINK - RATE LIMIT MIDDLEWARE (REDIS VERSION)
# ============================================================

import time
from typing import Dict, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config import settings
from ..core.redis import redis_client

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
    Middleware to rate limit requests per IP using Redis.
    
    Features:
    - Different limits for different endpoints
    - IP-based tracking (supports proxies)
    - Redis storage (persistent across restarts)
    - Rate limit headers in responses
    - Returns 429 when limit exceeded
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
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
        max_requests = limit_config['requests']
        period = limit_config['period']
        
        # Redis key for this client and endpoint
        redis_key = f"rate_limit:{client_id}:{request.url.path}"
        
        # Check rate limit using Redis
        is_allowed, remaining, reset_time = await self._check_rate_limit_redis(
            redis_key, 
            max_requests, 
            period
        )
        
        if not is_allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": 429,
                        "message": f"Rate limit exceeded. Maximum {max_requests} requests per {period} seconds.",
                        "reset_at": reset_time,
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time())),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
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
    
    async def _check_rate_limit_redis(
        self, 
        redis_key: str, 
        max_requests: int, 
        period: int
    ) -> Tuple[bool, int, float]:
        """
        Check if client is rate limited using Redis.
        
        Returns:
            (is_allowed, remaining_requests, reset_time)
        """
        try:
            # Check if Redis is available
            if not await redis_client.ping():
                # Redis unavailable - allow request (fail open)
                return True, max_requests, time.time() + period
            
            # Get current count from Redis
            current_count = await redis_client.get(redis_key)
            
            if current_count is None:
                # First request, set to 1 with expiry
                await redis_client.set(redis_key, 1, ex=period)
                return True, max_requests - 1, time.time() + period
            
            # Increment count
            new_count = await redis_client.incr(redis_key, ex=period)
            
            # Get TTL for reset time
            ttl = await redis_client.ttl(redis_key)
            reset_time = time.time() + ttl if ttl > 0 else time.time() + period
            
            if new_count > max_requests:
                return False, 0, reset_time
            
            remaining = max_requests - new_count
            return True, remaining, reset_time
            
        except Exception as e:
            # If Redis fails, allow request (fail open)
            return True, max_requests, time.time() + period