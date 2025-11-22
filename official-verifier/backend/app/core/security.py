"""Security utilities for API key authentication and rate limiting."""
import bcrypt
import redis.asyncio as redis
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional
import time

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    """Hash an API key using bcrypt."""
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def verify_api_key(key: str, hashed: str) -> bool:
    """Verify an API key against its hash."""
    return bcrypt.checkpw(key.encode(), hashed.encode())


class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(self, api_key_id: str, rate_per_min: int) -> bool:
        """
        Check if request is within rate limit using token bucket.
        Returns True if allowed, False if rate limited.
        """
        window = int(time.time() / 60)  # 1-minute windows
        key = f"rl:{api_key_id}:{window}"
        
        current = await self.redis.get(key)
        if current is None:
            await self.redis.setex(key, 65, 1)
            return True
        
        count = int(current)
        if count >= rate_per_min:
            return False
        
        await self.redis.incr(key)
        return True


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header),
    repo = None,
    rate_limiter: RateLimiter = None
) -> dict:
    """
    Validate API key and check rate limits.
    Returns API key info if valid.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate API key
    key_info = await repo.get_api_key_by_value(api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not key_info["active"]:
        raise HTTPException(status_code=401, detail="API key inactive")
    
    # Check rate limit
    rate_per_min = key_info.get("rate_per_min", settings.RATE_LIMIT_FREE_PER_MIN)
    allowed = await rate_limiter.check_rate_limit(str(key_info["id"]), rate_per_min)
    
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return key_info
