# ============================================================
# AETHER LINK - CONFIGURATION
# ============================================================

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator, ValidationError
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
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ============================================================
    # DATABASE
    # ============================================================
    
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with postgresql://")
        return v
    
    # ============================================================
    # JWT AUTHENTICATION
    # ============================================================
    
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="JWT signing secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    @validator("JWT_SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Ensure JWT secret is strong."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    # ============================================================
    # CORS
    # ============================================================
    
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # ============================================================
    # RATE LIMITING
    # ============================================================
    
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # ============================================================
    # FILE UPLOADS
    # ============================================================
    
    MAX_FILE_SIZE_MB: int = 20
    MAX_REQUEST_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "pptx", "doc", "docx"]
    
    # ============================================================
    # CLOUD STORAGE (Future)
    # ============================================================
    
    STORAGE_PROVIDER: str = "supabase"  # supabase, s3, cloudinary
    STORAGE_BUCKET: Optional[str] = None
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_REGION: Optional[str] = None
    
    # ============================================================
    # EMAIL (Future)
    # ============================================================
    
    EMAIL_PROVIDER: str = "sendgrid"  # sendgrid, resend
    EMAIL_FROM: str = "noreply@aetherlink.com"
    SENDGRID_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    
    # ============================================================
    # ADMIN
    # ============================================================
    
    ADMIN_EMAIL: str = "ceo@aetherlink.com"
    ADMIN_PHONE: str = "+92300xxxxxxx"
    
    # ============================================================
    # ZOOM INTEGRATION (Future)
    # ============================================================
    
    ZOOM_ACCOUNT_ID: Optional[str] = None
    ZOOM_CLIENT_ID: Optional[str] = None
    ZOOM_CLIENT_SECRET: Optional[str] = None
    
    # ============================================================
    # EASY PAISA (Manual Verification)
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
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# ============================================================
# SINGLETON INSTANCE
# ============================================================

try:
    settings = Settings()
    print(f"✅ Config loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Database: {settings.DATABASE_URL[:30]}...")
except ValidationError as e:
    print("❌ Configuration error:")
    for error in e.errors():
        print(f"   - {error['loc'][0]}: {error['msg']}")
    raise