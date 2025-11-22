"""Seed database with example data."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.base import db
from app.db.repository import repository
from app.services.scoring import SIGNAL_PRESETS


async def seed_database():
    """Seed database with example entities."""
    await db.connect()
    
    try:
        print("Seeding database...")
        
        # Create HDFC Bank entity
        print("\nCreating HDFC Bank...")
        hdfc_id = await repository.upsert_entity("HDFC Bank", "bank", "IN")
        
        # Add official domain
        hdfc_domain_id = await repository.upsert_domain(hdfc_id, "hdfcbank.com", is_primary=True)
        
        # Add Wikipedia verification
        wiki_source_id = await repository.upsert_source(
            "wikipedia",
            "https://en.wikipedia.org/wiki/HDFC_Bank",
            "Wikipedia"
        )
        await repository.create_verification(
            hdfc_id,
            wiki_source_id,
            45.0,
            1.5,
            hdfc_domain_id,
            {"verified": True}
        )
        
        # Add App Store verification
        appstore_source_id = await repository.upsert_source(
            "appstore",
            "https://apps.apple.com/app/hdfcbank-mobilebankingapp/id422638379",
            "Apple App Store"
        )
        await repository.create_verification(
            hdfc_id,
            appstore_source_id,
            50.0,
            1.5,
            hdfc_domain_id,
            {"verified": True}
        )
        
        # Add lookalike domain
        await db.execute(
            """INSERT INTO lookalike_domains (entity_id, domain, algorithm, distance, flagged)
               VALUES ($1, $2, $3, $4, $5)""",
            hdfc_id, "hdfcbank-secure.co", "levenshtein", 1, True
        )
        
        # Recompute score
        score = await repository.recompute_entity_score(hdfc_id)
        print(f"HDFC Bank created with confidence score: {score}")
        
        # Update official_domain_id
        await db.execute(
            "UPDATE entities SET official_domain_id = $1 WHERE id = $2",
            hdfc_domain_id, hdfc_id
        )
        
        # Create PayPal entity
        print("\nCreating PayPal...")
        paypal_id = await repository.upsert_entity("PayPal", "payment", "US")
        
        paypal_domain_id = await repository.upsert_domain(paypal_id, "paypal.com", is_primary=True)
        
        wiki_paypal_source = await repository.upsert_source(
            "wikipedia",
            "https://en.wikipedia.org/wiki/PayPal",
            "Wikipedia"
        )
        await repository.create_verification(
            paypal_id,
            wiki_paypal_source,
            45.0,
            1.5,
            paypal_domain_id,
            {"verified": True}
        )
        
        score = await repository.recompute_entity_score(paypal_id)
        print(f"PayPal created with confidence score: {score}")
        
        await db.execute(
            "UPDATE entities SET official_domain_id = $1 WHERE id = $2",
            paypal_domain_id, paypal_id
        )
        
        # Create test user and API key
        print("\nCreating test user and API key...")
        user_id = await db.fetchval(
            """INSERT INTO users (email, role)
               VALUES ($1, $2)
               ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
               RETURNING id""",
            "test@example.com", "consumer"
        )
        
        # Create API key: "test-api-key-12345"
        from app.core.security import hash_api_key
        key_hash = hash_api_key("test-api-key-12345")
        
        await db.execute(
            """INSERT INTO api_keys (user_id, key_hash, name, rate_per_min, active)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT DO NOTHING""",
            user_id, key_hash, "Test API Key", 100, True
        )
        
        print("Test API Key: test-api-key-12345")
        
        # Refresh materialized view
        print("\nRefreshing materialized view...")
        await repository.refresh_materialized_view()
        
        print("\n✅ Database seeded successfully!")
        print("\nTest the API with:")
        print('curl -X POST http://localhost:8000/v1/lookup \\')
        print('  -H "X-API-Key: test-api-key-12345" \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"query": "HDFC Bank"}\'')
    
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_database())
