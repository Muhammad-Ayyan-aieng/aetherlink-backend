# ============================================================
# AETHER LINK - SECURITY HEADERS MIDDLEWARE
# ============================================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Strict-Transport-Security (HSTS) - production only
    - Content-Security-Policy (CSP)
    - Permissions-Policy
    - Cache-Control
    - Remove Server header
    
    Usage:
        app.add_middleware(SecurityHeadersMiddleware)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.
        """
        response = await call_next(request)
        
        # ============================================================
        # ALWAYS ADD THESE HEADERS
        # ============================================================
        
        # Prevent MIME type sniffing (XSS protection)
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable browser XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # ============================================================
        # REMOVE SENSITIVE HEADERS
        # ============================================================
        
        # Remove Server header (hide server info from attackers)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Remove X-Powered-By (hide framework info)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        # ============================================================
        # HSTS (STRICT-TRANSPORT-SECURITY) - PRODUCTION ONLY
        # ============================================================
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # ============================================================
        # CONTENT-SECURITY-POLICY (CSP)
        # ============================================================
        
        response.headers["Content-Security-Policy"] = self._get_csp_policy()
        
        # ============================================================
        # PERMISSIONS-POLICY
        # ============================================================
        
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "screen-wake-lock=()"
        )
        
        # ============================================================
        # CACHE CONTROL
        # ============================================================
        
        # Prevent caching of API responses
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    
    def _get_csp_policy(self) -> str:
        """
        Get Content-Security-Policy based on environment.
        """
        if settings.ENVIRONMENT == "production":
            return self._get_production_csp()
        return self._get_development_csp()
    
    def _get_production_csp(self) -> str:
        """
        Strict CSP for production.
        Only allows resources from same-origin and trusted domains.
        """
        policy = [
            # Default: only same-origin
            "default-src 'self'",
            
            # Images: same-origin, Supabase storage, data URIs
            "img-src 'self' https://*.supabase.co data:",
            
            # Fonts: same-origin, Google Fonts
            "font-src 'self' https://fonts.gstatic.com",
            
            # Styles: same-origin, Google Fonts, unsafe-inline (for some UIs)
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            
            # Scripts: same-origin, unsafe-inline (for Vue/React)
            "script-src 'self' 'unsafe-inline'",
            
            # Connect: same-origin, Supabase
            "connect-src 'self' https://*.supabase.co",
            
            # No iframe embedding
            "frame-ancestors 'none'",
            
            # Base URI: only same-origin
            "base-uri 'self'",
            
            # Form actions: only same-origin
            "form-action 'self'",
            
            # Upgrade insecure requests
            "upgrade-insecure-requests",
        ]
        
        return "; ".join(policy)
    
    def _get_development_csp(self) -> str:
        """
        Loose CSP for development.
        Allows everything for easier debugging.
        """
        policy = [
            # Default: allow everything
            "default-src *",
            
            # Images: any source
            "img-src * data:",
            
            # Fonts: any source
            "font-src *",
            
            # Styles: any source, unsafe-inline
            "style-src * 'unsafe-inline'",
            
            # Scripts: any source, unsafe-inline, unsafe-eval (for HMR)
            "script-src * 'unsafe-inline' 'unsafe-eval'",
            
            # Connect: any source
            "connect-src *",
            
            # Allow iframes in dev (for testing)
            "frame-ancestors *",
            
            # Base URI: only same-origin
            "base-uri 'self'",
        ]
        
        return "; ".join(policy)