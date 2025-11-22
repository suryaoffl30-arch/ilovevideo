"""Public API endpoints."""
from fastapi import APIRouter, HTTPException
from uuid import UUID
import time
import redis.asyncio as redis
import json

from app.schemas.pydantic_models import (
    LookupRequest, LookupResponse, SubmissionRequest, SubmissionResponse,
    EntityDetailResponse, SimilarDomainResponse
)
from app.db.repository import repository
from app.core.config import settings
from app.services.scoring import compute_score, calculate_risk_level
from app.services.harvester import normalize_and_extract_domain

router = APIRouter()

# Redis client for caching
redis_client = None


async def get_redis():
    """Get Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


@router.post("/lookup", response_model=LookupResponse)
async def lookup_entity(request: LookupRequest):
    """Look up an entity by name or domain."""
    start_time = time.time()
    redis_conn = await get_redis()
    
    try:
        # Determine search type
        if request.domain:
            domain = normalize_and_extract_domain(request.domain) or request.domain
            cache_key = f"lookup:domain:{domain}"
            entity = await repository.get_entity_by_domain(domain)
        elif request.query:
            cache_key = f"lookup:query:{request.query.lower()}"
            
            # Check cache
            cached = await redis_conn.get(cache_key)
            if cached:
                return LookupResponse(ok=True, data=json.loads(cached))
            
            # Search by name
            entities = await repository.search_entities_by_name(request.query)
            if not entities:
                return LookupResponse(ok=True, data=None)
            
            entity = entities[0]  # Take best match
        else:
            raise HTTPException(status_code=400, detail="Either query or domain must be provided")
        
        if not entity:
            return LookupResponse(ok=True, data=None)
        
        # Get entity details
        entity_id = entity['id']
        domains = await repository.get_entity_domains(entity_id)
        verifications = await repository.get_entity_verifications(entity_id)
        lookalikes = await repository.get_lookalike_domains(entity_id)
        
        # Compute score
        score, risk_level = compute_score(verifications, lookalikes)
        
        # Get official domain
        official_domain = None
        for d in domains:
            if d.get('is_primary'):
                official_domain = d['domain']
                break
        if not official_domain and domains:
            official_domain = domains[0]['domain']
        
        # Build verification sources
        verification_sources = []
        for v in verifications:
            if v.get('status') in ['verified', 'needs_review']:
                verification_sources.append({
                    'source_type': v.get('source_type'),
                    'url': v.get('source_url'),
                    'score': round(v['score_contrib'] * v['weight'], 2)
                })
        
        # Build similar domains
        similar_domains = []
        for lookalike in lookalikes:
            risk = 'high' if lookalike.get('flagged') else 'medium'
            similar_domains.append({
                'domain': lookalike['domain'],
                'risk': risk,
                'similarity': 1.0 - (lookalike.get('distance', 0) / 10.0)
            })
        
        # Get last verified timestamp
        last_verified_at = None
        if verifications:
            last_verified_at = max(v.get('verified_at') for v in verifications if v.get('verified_at'))
        
        response_data = {
            'entity_id': str(entity_id),
            'name': entity['name'],
            'official_domain': official_domain,
            'confidence_score': score,
            'risk_level': risk_level,
            'verification_sources': verification_sources,
            'similar_domains': similar_domains,
            'last_verified_at': last_verified_at.isoformat() if last_verified_at else None
        }
        
        # Cache result for 90 seconds
        await redis_conn.setex(cache_key, 90, json.dumps(response_data, default=str))
        
        return LookupResponse(ok=True, data=response_data)
    
    except Exception as e:
        return LookupResponse(ok=False, error=str(e))


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
async def get_entity_details(entity_id: UUID):
    """Get full entity details including all domains and verifications."""
    entity = await repository.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    domains = await repository.get_entity_domains(entity_id)
    verifications = await repository.get_entity_verifications(entity_id)
    lookalikes = await repository.get_lookalike_domains(entity_id)
    
    # Compute score
    score, risk_level = compute_score(verifications, lookalikes)
    
    # Get official domain
    official_domain = None
    for d in domains:
        if d.get('is_primary'):
            official_domain = d['domain']
            break
    
    # Get last verified
    last_verified_at = None
    if verifications:
        last_verified_at = max(v.get('verified_at') for v in verifications if v.get('verified_at'))
    
    # Build similar domains
    similar_domains = []
    for lookalike in lookalikes:
        risk = 'high' if lookalike.get('flagged') else 'medium'
        similar_domains.append(SimilarDomainResponse(
            domain=lookalike['domain'],
            risk=risk,
            similarity=1.0 - (lookalike.get('distance', 0) / 10.0),
            flagged=lookalike.get('flagged', False)
        ))
    
    return EntityDetailResponse(
        entity_id=entity_id,
        name=entity['name'],
        entity_type=entity.get('entity_type'),
        official_domain=official_domain,
        confidence_score=score,
        risk_level=risk_level,
        status=entity['status'],
        domains=[dict(d) for d in domains],
        verifications=[dict(v) for v in verifications],
        similar_domains=similar_domains,
        last_verified_at=last_verified_at,
        created_at=entity['created_at']
    )


@router.post("/submissions", response_model=SubmissionResponse)
async def create_submission(submission: SubmissionRequest):
    """Submit a new domain for verification."""
    submission_id = await repository.create_submission(
        submission.submitted_by,
        submission.entity_name,
        submission.domain,
        submission.evidence or {}
    )
    
    return SubmissionResponse(
        ok=True,
        submission_id=submission_id,
        status="pending"
    )


@router.post("/domains/check")
async def check_domain(request: LookupRequest):
    """Quick domain risk check."""
    if not request.domain:
        raise HTTPException(status_code=400, detail="Domain required")
    
    domain = normalize_and_extract_domain(request.domain) or request.domain
    
    # Check if domain exists
    entity = await repository.get_entity_by_domain(domain)
    
    if entity:
        return {
            'ok': True,
            'domain': domain,
            'known': True,
            'entity_name': entity['name'],
            'confidence_score': float(entity['confidence_score']),
            'risk_level': calculate_risk_level(float(entity['confidence_score']))
        }
    else:
        return {
            'ok': True,
            'domain': domain,
            'known': False,
            'risk_level': 'unknown',
            'message': 'Domain not in verified database'
        }
