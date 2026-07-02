# ============================================================
# AETHER LINK - MAIN APPLICATION
# ============================================================

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.config import settings
from .core.database import engine, Base, test_connection, get_connection_info

# Import middleware
from .middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# LIFESPAN EVENTS
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🗄️  Database: {settings.DATABASE_URL[:50]}...")
    
    # Test database connection (don't crash if down)
    try:
        status = test_connection()
        logger.info(f"   {status}")
        if "✅" in status:
            info = get_connection_info()
            logger.info(f"   Pool size: {info.get('pool_size')}")
        
        # Import models here to avoid circular imports
        from .models import (
            User, Course, Session, Enrollment,
            Attendance, Payment, CourseMaterial, TeacherInvitation
        )
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified")
    except Exception as e:
        logger.error(f"⚠️ Database connection issue: {e}")
        logger.warning("⚠️ App will start but database is unavailable")
    
    logger.info("=" * 60)
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("🛑 Shutting down Aether Link API...")
    engine.dispose()
    logger.info("✅ Database connections closed")


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🚀 Aether Link - Online Learning Management System
    
    ## Features
    - 🔐 Authentication & Authorization (JWT)
    - 📚 Course Management
    - 👨‍🏫 Teacher Invitations
    - 📝 Attendance Tracking
    - 💳 Payment Processing (EasyPaisa)
    - 📊 Admin Dashboard
    - 📎 Course Materials
    
    ## User Roles
    - **Admin**: Full system access
    - **Teacher**: Create courses, manage sessions, mark attendance
    - **Student**: Enroll, attend sessions, access materials
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================
# MIDDLEWARE (Order Matters!)
# ============================================================

# 1. Request ID - FIRST (generates ID before anything else)
app.add_middleware(RequestIDMiddleware)

# 2. Logging - SECOND (uses request_id for logging)
app.add_middleware(LoggingMiddleware)

# 3. Rate Limit - THIRD (blocks before processing)
app.add_middleware(RateLimitMiddleware)

# 4. Security Headers - FOURTH (adds headers to response)
app.add_middleware(SecurityHeadersMiddleware)

# 5. CORS - LAST (handles cross-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Total-Count",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-Process-Time",
        "X-Request-ID",
        "X-Response-Time-MS",
    ],
)


# ============================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with detailed field errors.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": errors,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions.
    """
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    
    # In production, don't expose internal errors
    if settings.ENVIRONMENT == "production":
        message = "An internal server error occurred"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": message,
                "path": request.url.path,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


# ============================================================
# HEALTH CHECK ENDPOINTS
# ============================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    db_status = test_connection()
    
    return {
        "status": "healthy" if "✅" in db_status else "unhealthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system information.
    """
    db_status = test_connection()
    db_info = get_connection_info()
    
    return {
        "status": "healthy" if "✅" in db_status else "unhealthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "status": db_status,
            "pool_size": db_info.get("pool_size"),
            "checked_in": db_info.get("checked_in_connections"),
            "overflow": db_info.get("overflow"),
            "total": db_info.get("total_connections"),
        },
        "rate_limits": {
            "auth": "10/minute",
            "admin": "30/minute",
            "default": "100/minute",
            "sensitive": "5/minute",
        }
    }


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api": "/api/v1",
    }


# ============================================================
# INCLUDE API ROUTERS
# ============================================================

# Import router after app creation to avoid circular imports
from .api.v1.router import router as api_v1_router
app.include_router(api_v1_router)


# ============================================================
# RUN APPLICATION (Development)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )