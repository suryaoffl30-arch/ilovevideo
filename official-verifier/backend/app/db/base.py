"""Database connection management."""
import asyncpg
from typing import Optional

from app.core.config import settings


class Database:
    """Database connection pool manager."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool."""
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_DSN,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def execute(self, query: str, *args):
        """Execute a query."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch a single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch a single value."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


db = Database()
