"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# Request models
class LookupRequest(BaseModel):
    """Request model for entity lookup."""
    query: Optional[str] = None
    domain: Optional[str] = None


class SubmissionRequest(BaseModel):
    """Request model for domain submission."""
    submitted_by: str
    entity_name: str
    domain: str
    evidence: Optional[Dict[str, Any]] = None


class ClaimInitiateRequest(BaseModel):
    """Request model for initiating brand claim."""
    entity_id: UUID
    domain: str
    method: str = Field(..., pattern="^(dns|html|email)$")


class ClaimVerifyRequest(BaseModel):
    """Request model for verifying brand claim."""
    claim_id: UUID
    verification_code: Optional[str] = None


class EntityCreateRequest(BaseModel):
    """Request model for creating entity (admin)."""
    name: str
    entity_type: Optional[str] = None
    country_iso2: Optional[str] = None
    description: Optional[str] = None


class VerificationCreateRequest(BaseModel):
    """Request model for creating verification (admin)."""
    entity_id: UUID
    source_type: str
    url: str
    score_contrib: float
    weight: float
    domain_id: Optional[UUID] = None
    evidence: Optional[Dict[str, Any]] = None


# Response models
class VerificationSourceResponse(BaseModel):
    """Verification source in response."""
    source_type: str
    url: Optional[str]
    score: float
    display_name: Optional[str] = None


class SimilarDomainResponse(BaseModel):
    """Similar/lookalike domain in response."""
    domain: str
    risk: str
    similarity: float
    flagged: bool


class LookupResponse(BaseModel):
    """Response model for entity lookup."""
    ok: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class EntityDetailResponse(BaseModel):
    """Detailed entity response."""
    entity_id: UUID
    name: str
    entity_type: Optional[str]
    official_domain: Optional[str]
    confidence_score: float
    risk_level: str
    status: str
    domains: List[Dict[str, Any]]
    verifications: List[Dict[str, Any]]
    similar_domains: List[SimilarDomainResponse]
    last_verified_at: Optional[datetime]
    created_at: datetime


class SubmissionResponse(BaseModel):
    """Response for submission creation."""
    ok: bool = True
    submission_id: UUID
    status: str = "pending"


class ErrorResponse(BaseModel):
    """Error response model."""
    ok: bool = False
    error: str
    detail: Optional[str] = None
