"""Database repository for data access."""
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid

from app.db.base import db
from app.core.security import verify_api_key


class Repository:
    """Data access layer."""
    
    async def get_api_key_by_value(self, key: str) -> Optional[Dict]:
        """Get API key info by validating the key value."""
        rows = await db.fetch(
            "SELECT id, user_id, key_hash, rate_per_min, active FROM api_keys WHERE active = TRUE"
        )
        
        for row in rows:
            if verify_api_key(key, row["key_hash"]):
                return dict(row)
        
        return None
    
    async def log_usage(self, api_key_id: UUID, endpoint: str, ip: str, status: int, latency_ms: int):
        """Log API usage asynchronously."""
        await db.execute(
            """INSERT INTO usage_logs (api_key_id, endpoint, ip, http_status, latency_ms)
               VALUES ($1, $2, $3, $4, $5)""",
            api_key_id, endpoint, ip, status, latency_ms
        )
    
    async def search_entities_by_name(self, query: str, limit: int = 10) -> List[Dict]:
        """Search entities by name using trigram similarity."""
        rows = await db.fetch(
            """SELECT id, name, normalized_name, entity_type, confidence_score, official_domain_id
               FROM entities
               WHERE normalized_name % $1
               ORDER BY similarity(normalized_name, $1) DESC
               LIMIT $2""",
            query.lower(), limit
        )
        return [dict(row) for row in rows]
    
    async def get_entity_by_id(self, entity_id: UUID) -> Optional[Dict]:
        """Get entity by ID."""
        row = await db.fetchrow(
            "SELECT * FROM entities WHERE id = $1",
            entity_id
        )
        return dict(row) if row else None
    
    async def get_entity_by_domain(self, domain: str) -> Optional[Dict]:
        """Get entity by domain."""
        row = await db.fetchrow(
            """SELECT e.* FROM entities e
               JOIN domains d ON d.entity_id = e.id
               WHERE d.domain = $1 AND d.active = TRUE
               LIMIT 1""",
            domain
        )
        return dict(row) if row else None
    
    async def get_entity_domains(self, entity_id: UUID) -> List[Dict]:
        """Get all domains for an entity."""
        rows = await db.fetch(
            "SELECT * FROM domains WHERE entity_id = $1 ORDER BY is_primary DESC, created_at",
            entity_id
        )
        return [dict(row) for row in rows]
    
    async def get_entity_verifications(self, entity_id: UUID) -> List[Dict]:
        """Get all verifications for an entity with source info."""
        rows = await db.fetch(
            """SELECT v.*, s.source_type, s.url as source_url, s.display_name
               FROM verifications v
               JOIN sources s ON v.source_id = s.id
               WHERE v.entity_id = $1
               ORDER BY v.verified_at DESC""",
            entity_id
        )
        return [dict(row) for row in rows]
    
    async def get_lookalike_domains(self, entity_id: UUID) -> List[Dict]:
        """Get lookalike domains for an entity."""
        rows = await db.fetch(
            """SELECT domain, algorithm, distance, flagged
               FROM lookalike_domains
               WHERE entity_id = $1 AND distance < 3
               ORDER BY distance, flagged DESC""",
            entity_id
        )
        return [dict(row) for row in rows]
    
    async def create_submission(self, submitted_by: str, entity_name: str, domain: str, evidence: Dict) -> UUID:
        """Create a new submission."""
        submission_id = await db.fetchval(
            """INSERT INTO submissions (submitted_by, entity_name, domain, evidence)
               VALUES ($1, $2, $3, $4)
               RETURNING id""",
            submitted_by, entity_name, domain, evidence
        )
        return submission_id
    
    async def upsert_entity(self, name: str, entity_type: str = None, country: str = None) -> UUID:
        """Create or update an entity."""
        # Check if entity exists
        existing = await db.fetchrow(
            "SELECT id FROM entities WHERE normalized_name = $1",
            name.lower()
        )
        
        if existing:
            return existing['id']
        
        # Create new entity
        entity_id = await db.fetchval(
            """INSERT INTO entities (name, normalized_name, entity_type, country_iso2)
               VALUES ($1, $2, $3, $4)
               RETURNING id""",
            name, name.lower(), entity_type, country
        )
        return entity_id
    
    async def upsert_domain(self, entity_id: UUID, domain: str, is_primary: bool = False) -> UUID:
        """Create or update a domain."""
        domain_id = await db.fetchval(
            """INSERT INTO domains (entity_id, domain, is_primary)
               VALUES ($1, $2, $3)
               ON CONFLICT (domain) DO UPDATE SET updated_at = NOW()
               RETURNING id""",
            entity_id, domain, is_primary
        )
        return domain_id
    
    async def upsert_source(self, source_type: str, url: str, display_name: str = None) -> UUID:
        """Create or update a source."""
        source_id = await db.fetchval(
            """INSERT INTO sources (source_type, url, display_name)
               VALUES ($1, $2, $3)
               ON CONFLICT DO NOTHING
               RETURNING id""",
            source_type, url, display_name
        )
        
        if not source_id:
            source_id = await db.fetchval(
                "SELECT id FROM sources WHERE source_type = $1 AND url = $2",
                source_type, url
            )
        
        return source_id
    
    async def create_verification(
        self, entity_id: UUID, source_id: UUID, score_contrib: float, 
        weight: float, domain_id: UUID = None, evidence: Dict = None
    ) -> UUID:
        """Create a verification record."""
        verification_id = await db.fetchval(
            """INSERT INTO verifications (entity_id, domain_id, source_id, score_contrib, weight, evidence)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id""",
            entity_id, domain_id, source_id, score_contrib, weight, evidence
        )
        return verification_id
    
    async def recompute_entity_score(self, entity_id: UUID) -> float:
        """Recompute and update entity confidence score."""
        score = await db.fetchval(
            "SELECT compute_entity_confidence($1)",
            entity_id
        )
        
        await db.execute(
            "UPDATE entities SET confidence_score = $1, updated_at = NOW() WHERE id = $2",
            score, entity_id
        )
        
        return float(score)
    
    async def refresh_materialized_view(self):
        """Refresh the materialized view."""
        await db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY api_entity_view")


repository = Repository()
