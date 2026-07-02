# ============================================================
# AETHER LINK - DATABASE CONNECTION
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import time

from .config import settings

# ============================================================
# ENGINE CONFIGURATION
# ============================================================

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,                    # Max permanent connections
    max_overflow=20,                 # Extra connections if needed
    pool_timeout=30,                 # Wait 30s before giving up
    pool_pre_ping=True,              # Check connection before using
    echo=settings.DEBUG,             # SQL logging in debug mode
    pool_recycle=3600,               # Recycle connections every hour
)

# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ============================================================
# BASE MODEL CLASS
# ============================================================

Base = declarative_base()


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Used in FastAPI endpoints via Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# CONNECTION TEST (HEALTH CHECK)
# ============================================================

def test_connection() -> str:
    """
    Test database connection.
    Returns success message or error.
    """
    try:
        with engine.connect() as conn:
            start_time = time.time()
            result = conn.execute(text("SELECT 1"))
            elapsed = (time.time() - start_time) * 1000
            return f"✅ Connected! (Response: {elapsed:.2f}ms)"
    except Exception as e:
        return f"❌ Connection failed: {str(e)}"


def get_connection_info() -> dict:
    """Get database connection information for debugging."""
    return {
        "database_url": settings.DATABASE_URL[:30] + "...",
        "pool_size": engine.pool.size(),
        "checked_in_connections": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "total_connections": engine.pool.size() + engine.pool.overflow(),  # Fix here
    }


# ============================================================
# INITIALIZATION
# ============================================================

def init_db() -> None:
    """
    Initialize database connection.
    Called on application startup.
    """
    print("🔗 Connecting to database...")
    status = test_connection()
    print(f"   {status}")
    if "✅" in status:
        info = get_connection_info()
        print(f"   Pool size: {info['pool_size']}")
        print(f"   Max overflow: {engine.pool._max_overflow}")
    else:
        print("   ⚠️ Database connection failed!")