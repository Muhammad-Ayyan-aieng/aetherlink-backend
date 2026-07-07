# ============================================================
# AETHER LINK - REDIS CLIENT
# ============================================================

import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for async operations."""
    
    def __init__(self):
        self.client = None
        self._connected = False

    async def connect(self):
        """Connect to Redis server."""
        try:
            self.client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            await self.client.ping()
            self._connected = True
            logger.info(f"✅ Redis connected to {settings.REDIS_URL}")
            return self.client
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._connected = False
            self.client = None
            return None

    async def disconnect(self):
        """Disconnect from Redis server."""
        if self.client:
            await self.client.close()
            self._connected = False
            logger.info("✅ Redis disconnected")

    async def ping(self):
        """Check if Redis is connected."""
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception:
            return False

    async def get(self, key):
        """Get value from Redis."""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(self, key, value, ex=None):
        """Set value in Redis with optional TTL."""
        if not self.client:
            return False
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def incr(self, key, ex=None):
        """Increment value in Redis and set TTL if provided."""
        if not self.client:
            return 0
        try:
            count = await self.client.incr(key)
            if ex:
                await self.client.expire(key, ex)
            return count
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0

    async def expire(self, key, seconds):
        """Set TTL for key."""
        if not self.client:
            return False
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    async def ttl(self, key):
        """Get TTL for key."""
        if not self.client:
            return -2
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -2

    async def delete(self, key):
        """Delete key from Redis."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False


# Singleton instance
redis_client = RedisClient()