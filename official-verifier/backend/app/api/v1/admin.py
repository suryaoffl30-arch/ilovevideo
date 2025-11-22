"""Admin API endpoints."""
from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.schemas.pydantic_models import (
    EntityCreateRequest, VerificationCreateRequest
)
from app.db.repository import repository
from app.services.scoring import SIGNAL_PRESETS

router = APIRouter()


@router.post("/entities")
async def create_entity(request: EntityCreateRequest):
    """Create or upsert an entity (admin only)."""
    entity_id = await repository.upsert_entity(
        request.name,
        request.entity_type,
        request.country_iso2
    )
    
    return {
        'ok': True,
        'entity_id': str(entity_id),
        'message': 'Entity created/updated'
    }


@router.post("/verifications")
async def create_verification(request: VerificationCreateRequest):
    """Add verification record (admin only)."""
    # Create source
    source_id = await repository.upsert_source(
        request.source_type,
        request.url,
        request.source_type.title()
    )
    
    # Create verification
    verification_id = await repository.create_verification(
        request.entity_id,
        source_id,
        request.score_contrib,
        request.weight,
        request.domain_id,
        request.evidence
    )
    
    # Recompute score
    new_score = await repository.recompute_entity_score(request.entity_id)
    
    return {
        'ok': True,
        'verification_id': str(verification_id),
        'new_confidence_score': new_score
    }


@router.post("/recompute/{entity_id}")
async def recompute_score(entity_id: UUID):
    """Recompute confidence score for an entity (admin only)."""
    entity = await repository.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    new_score = await repository.recompute_entity_score(entity_id)
    
    return {
        'ok': True,
        'entity_id': str(entity_id),
        'confidence_score': new_score
    }


@router.post("/refresh-view")
async def refresh_materialized_view():
    """Refresh materialized view (admin only)."""
    await repository.refresh_materialized_view()
    
    return {
        'ok': True,
        'message': 'Materialized view refreshed'
    }
