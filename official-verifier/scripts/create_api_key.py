"""Create a hashed API key for testing."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.base import db
from app.core.security import hash_api_key


async def create_api_key(key: str, name: str, rate_per_min: int = 30):
    """Create a new API key."""
    await db.connect()
    
    try:
        # Hash the key
        key_hash = hash_api_key(key)
        
        # Create test user if not exists
        user_id = await db.fetchval(
            """INSERT INTO users (email, role)
               VALUES ($1, $2)
               ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
               RETURNING id""",
            "admin@example.com", "admin"
        )
        
        # Insert API key
        api_key_id = await db.fetchval(
            """INSERT INTO api_keys (user_id, key_hash, name, rate_per_min, active)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id""",
            user_id, key_hash, name, rate_per_min, True
        )
        
        print(f"✅ API Key created successfully!")
        print(f"ID: {api_key_id}")
        print(f"Key: {key}")
        print(f"Name: {name}")
        print(f"Rate: {rate_per_min}/min")
        print(f"\nUse in requests:")
        print(f'  -H "X-API-Key: {key}"')
    
    finally:
        await db.disconnect()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_api_key.py <key> <name> [rate_per_min]")
        print("Example: python create_api_key.py my-secret-key 'Production Key' 100")
        sys.exit(1)
    
    key = sys.argv[1]
    name = sys.argv[2]
    rate = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    
    asyncio.run(create_api_key(key, name, rate))
