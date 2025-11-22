-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create entities table
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    normalized_name CITEXT,
    entity_type TEXT,
    country_iso2 CHAR(2),
    description TEXT,
    official_domain_id UUID,
    status TEXT DEFAULT 'pending',
    confidence_score NUMERIC(5,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entities_normalized_name ON entities USING gin(normalized_name gin_trgm_ops);
CREATE INDEX idx_entities_status ON entities(status);
CREATE INDEX idx_entities_confidence ON entities(confidence_score DESC);

-- Create domains table
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    domain TEXT UNIQUE NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    whois_created_at TIMESTAMPTZ,
    registrar TEXT,
    https_supported BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_domains_entity_id ON domains(entity_id);
CREATE INDEX idx_domains_domain ON domains USING gin(domain gin_trgm_ops);
CREATE INDEX idx_domains_active ON domains(active) WHERE active = TRUE;

-- Create sources table
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL,
    url TEXT,
    display_name TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sources_type ON sources(source_type);

-- Create verifications table
CREATE TABLE verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    domain_id UUID,
    source_id UUID NOT NULL,
    status TEXT DEFAULT 'verified',
    score_contrib NUMERIC NOT NULL,
    weight NUMERIC NOT NULL,
    evidence JSONB,
    verified_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_verifications_entity_id ON verifications(entity_id);
CREATE INDEX idx_verifications_status ON verifications(status);
CREATE INDEX idx_verifications_expires ON verifications(expires_at);

-- Create lookalike_domains table
CREATE TABLE lookalike_domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL,
    domain TEXT NOT NULL,
    algorithm TEXT,
    distance INT,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lookalike_entity_id ON lookalike_domains(entity_id);
CREATE INDEX idx_lookalike_flagged ON lookalike_domains(flagged) WHERE flagged = TRUE;

-- Create submissions table
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submitted_by TEXT,
    entity_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    evidence JSONB,
    status TEXT DEFAULT 'pending',
    reviewer_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX idx_submissions_status ON submissions(status);

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'consumer',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create api_keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    key_hash TEXT NOT NULL,
    name TEXT,
    rate_per_min INT DEFAULT 30,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_active ON api_keys(active) WHERE active = TRUE;

-- Create usage_logs table
CREATE TABLE usage_logs (
    id BIGSERIAL PRIMARY KEY,
    api_key_id UUID,
    endpoint TEXT,
    ip INET,
    http_status INT,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_logs_api_key ON usage_logs(api_key_id);
CREATE INDEX idx_usage_logs_created ON usage_logs(created_at DESC);

-- Add foreign key constraints
ALTER TABLE entities ADD CONSTRAINT fk_entities_official_domain 
    FOREIGN KEY (official_domain_id) REFERENCES domains(id);

ALTER TABLE domains ADD CONSTRAINT fk_domains_entity 
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;

ALTER TABLE verifications ADD CONSTRAINT fk_verifications_entity 
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;

ALTER TABLE verifications ADD CONSTRAINT fk_verifications_domain 
    FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE SET NULL;

ALTER TABLE verifications ADD CONSTRAINT fk_verifications_source 
    FOREIGN KEY (source_id) REFERENCES sources(id);

ALTER TABLE lookalike_domains ADD CONSTRAINT fk_lookalike_entity 
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE;

ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_user 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for updated_at
CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domains_updated_at BEFORE UPDATE ON domains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create compute_entity_confidence function
CREATE OR REPLACE FUNCTION compute_entity_confidence(entity_uuid UUID)
RETURNS NUMERIC(5,2) AS $$
DECLARE
    score_sum NUMERIC := 0;
    lookalike_penalty NUMERIC := 0;
    final_score NUMERIC;
BEGIN
    -- Sum contributions from verifications
    SELECT COALESCE(SUM(
        CASE 
            WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN score_contrib * weight * 0.5
            ELSE score_contrib * weight
        END
    ), 0) INTO score_sum
    FROM verifications
    WHERE entity_id = entity_uuid 
        AND status IN ('verified', 'needs_review');
    
    -- Apply lookalike penalty
    SELECT CASE WHEN COUNT(*) > 0 THEN 40 ELSE 0 END INTO lookalike_penalty
    FROM lookalike_domains
    WHERE entity_id = entity_uuid 
        AND flagged = TRUE 
        AND distance < 2;
    
    final_score := score_sum - lookalike_penalty;
    
    -- Cap between 0 and 100
    IF final_score > 100 THEN
        final_score := 100;
    ELSIF final_score < 0 THEN
        final_score := 0;
    END IF;
    
    RETURN final_score;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for fast entity lookups
CREATE MATERIALIZED VIEW api_entity_view AS
SELECT 
    e.id,
    e.name,
    e.normalized_name,
    e.entity_type,
    e.country_iso2,
    e.status,
    e.confidence_score,
    d.domain as official_domain,
    d.https_supported,
    e.created_at,
    e.updated_at
FROM entities e
LEFT JOIN domains d ON e.official_domain_id = d.id;

CREATE UNIQUE INDEX idx_api_entity_view_id ON api_entity_view(id);
CREATE INDEX idx_api_entity_view_name ON api_entity_view USING gin(normalized_name gin_trgm_ops);
