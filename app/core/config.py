# ============================================================
# AETHER LINK - CONFIGURATION
# ============================================================

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ============================================================
    # APP CONFIGURATION
    # ============================================================
    
    APP_NAME: str = "Aether Link API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # ============================================================
    # DATABASE
    # ============================================================
    
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with postgresql://")
        return v
    
    # ============================================================
    # JWT AUTHENTICATION
    # ============================================================
    
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============================================================
    # CORS
    # ============================================================
    
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://aetherlink-frontend.onrender.com",
            "https://aetherlink.vercel.app",
        ]
    )
    
    # ============================================================
    # RATE LIMITING
    # ============================================================
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # ============================================================
    # FILE UPLOADS
    # ============================================================
    
    MAX_FILE_SIZE_MB: int = 20
    MAX_REQUEST_SIZE_MB: int = 10
    
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "pptx", "doc", "docx", 
        "png", "jpg", "jpeg", "gif", "webp",
        "txt"
    ]
    
    # ============================================================
    # SUPABASE STORAGE
    # ============================================================
    
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service role key")
    SUPABASE_BUCKET: str = Field(default="course-materials")
    
    ALLOWED_MIME_TYPES: List[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
            "text/plain"
        ]
    )
    
    SIGNED_URL_EXPIRY: int = Field(default=60)
    
    # ============================================================
    # ADMIN
    # ============================================================
    
    ADMIN_EMAIL: str = "ceo@aetherlink.com"
    ADMIN_PHONE: str = "+92300xxxxxxx"
    
    # ============================================================
    # EMAIL
    # ============================================================
    
    EMAIL_PROVIDER: str = "sendgrid"
    EMAIL_FROM: str = "noreply@aetherlink.com"
    REPLY_TO: str = "support@aetherlink.com"  # ✅ ADDED: Reply-To email address
    SENDGRID_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    
    # ============================================================
    # REDIS CONFIGURATION
    # ============================================================
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    
    # ============================================================
    # ZOOM
    # ============================================================
    
    ZOOM_ACCOUNT_ID: Optional[str] = None
    ZOOM_CLIENT_ID: Optional[str] = None
    ZOOM_CLIENT_SECRET: Optional[str] = None
    ZOOM_WEBHOOK_SECRET: Optional[str] = None
    
    # ============================================================
    # EASY PAISA
    # ============================================================
    
    EASY_PAISA_ACCOUNT: str = "03XX-XXXXXXX"
    EASY_PAISA_HOLDER: str = "Aether Link Pvt Ltd"
    
    # ============================================================
    # LOGGING
    # ============================================================
    
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    
    # ============================================================
    # VALIDATION ON STARTUP
    # ============================================================
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("ALLOWED_ORIGINS cannot be empty")
        if "*" in v:
            raise ValueError("ALLOWED_ORIGINS must not include '*'")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# ============================================================
# SINGLETON INSTANCE
# ============================================================

try:
    settings = Settings()
    print(f"✅ Config loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Database: {settings.DATABASE_URL[:30]}...")
    print(f"   Supabase Storage: {settings.SUPABASE_BUCKET}")
    print(f"   Redis: {settings.REDIS_URL}")
    print(f"   Email From: {settings.EMAIL_FROM}")      # ✅ Added
    print(f"   Reply To: {settings.REPLY_TO}")          # ✅ Added
except ValidationError as e:
    print("❌ Configuration error:")
    for error in e.errors():
        print(f"   - {error['loc'][0]}: {error['msg']}")
    raise