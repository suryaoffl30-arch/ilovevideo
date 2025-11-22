"""Database models documentation.

This file documents the database schema.
Actual tables are created via SQL migrations.
"""

# entities table
# - id: uuid primary key
# - name: text not null
# - normalized_name: citext
# - entity_type: text (company, government, ngo, etc.)
# - country_iso2: char(2)
# - description: text
# - official_domain_id: uuid foreign key to domains
# - status: text (pending, verified, flagged)
# - confidence_score: numeric(5,2)
# - created_at: timestamptz
# - updated_at: timestamptz

# domains table
# - id: uuid primary key
# - entity_id: uuid foreign key to entities
# - domain: text unique
# - is_primary: bool
# - active: bool
# - whois_created_at: timestamptz
# - registrar: text
# - https_supported: bool
# - created_at: timestamptz
# - updated_at: timestamptz

# sources table
# - id: uuid primary key
# - source_type: text (wikipedia, appstore, playstore, etc.)
# - url: text
# - display_name: text
# - metadata: jsonb
# - created_at: timestamptz

# verifications table
# - id: uuid primary key
# - entity_id: uuid foreign key
# - domain_id: uuid foreign key (nullable)
# - source_id: uuid foreign key
# - status: text (verified, needs_review, rejected)
# - score_contrib: numeric
# - weight: numeric
# - evidence: jsonb
# - verified_at: timestamptz
# - expires_at: timestamptz

# lookalike_domains table
# - id: uuid primary key
# - entity_id: uuid foreign key
# - domain: text
# - algorithm: text (levenshtein, homoglyph, etc.)
# - distance: int
# - flagged: bool

# submissions table
# - id: uuid primary key
# - submitted_by: text
# - entity_name: text
# - domain: text
# - evidence: jsonb
# - status: text (pending, approved, rejected)
# - reviewer_id: uuid
# - created_at: timestamptz
# - reviewed_at: timestamptz

# users table
# - id: uuid primary key
# - email: text unique
# - role: text (admin, reviewer, consumer)
# - created_at: timestamptz

# api_keys table
# - id: uuid primary key
# - user_id: uuid foreign key
# - key_hash: text
# - name: text
# - rate_per_min: int
# - active: bool
# - created_at: timestamptz
# - last_used_at: timestamptz

# usage_logs table
# - id: bigserial primary key
# - api_key_id: uuid
# - endpoint: text
# - ip: inet
# - http_status: int
# - latency_ms: int
# - created_at: timestamptz
