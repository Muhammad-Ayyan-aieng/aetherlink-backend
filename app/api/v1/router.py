# ============================================================
# AETHER LINK - API ROUTER V1
# ============================================================

from fastapi import APIRouter

# Import all routers
from .auth import router as auth_router
from .users import router as users_router
from .courses import router as courses_router
from .sessions import router as sessions_router
from .enrollments import router as enrollments_router
from .attendance import router as attendance_router  # ⭐ CRITICAL
from .payments import router as payments_router
from .materials import router as materials_router
from .invitations import router as invitations_router
from .admin import router as admin_router
# In app/api/v1/router.py, add:
from .applications import router as applications_router
# Add this import
from .webhooks import router as webhooks_router

# ============================================================
# MAIN ROUTER
# ============================================================

router = APIRouter(prefix="/api/v1")
router.include_router(applications_router)
router.include_router(webhooks_router)

# Include all routers
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(courses_router)
router.include_router(sessions_router)
router.include_router(enrollments_router)
router.include_router(attendance_router)  # ⭐ CRITICAL
router.include_router(payments_router)
router.include_router(materials_router)
router.include_router(invitations_router)
router.include_router(admin_router)

# ============================================================
# API ROOT
# ============================================================

@router.get("/", tags=["Root"])
def api_root():
    """
    API v1 root endpoint.
    """
    return {
        "message": "Aether Link API v1",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "courses": "/api/v1/courses",
            "sessions": "/api/v1/sessions",
            "enrollments": "/api/v1/enrollments",
            "attendance": "/api/v1/attendance",  # ⭐ CRITICAL
            "payments": "/api/v1/payments",
            "materials": "/api/v1/materials",
            "invitations": "/api/v1/invitations",
            "admin": "/api/v1/admin",
        },
    }