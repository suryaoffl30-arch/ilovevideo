"""
Quick local demo without Docker.
This creates an in-memory demo with mock data.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(title="Official Website Verifier - Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database
MOCK_ENTITIES = {
    "hdfc": {
        "entity_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "HDFC Bank",
        "official_domain": "hdfcbank.com",
        "confidence_score": 100.0,
        "risk_level": "none",
        "verification_sources": [
            {"source_type": "wikipedia", "url": "https://en.wikipedia.org/wiki/HDFC_Bank", "score": 67.5},
            {"source_type": "appstore", "url": "https://apps.apple.com/app/hdfcbank", "score": 75.0}
        ],
        "similar_domains": [
            {"domain": "hdfcbank-secure.co", "risk": "high", "similarity": 0.92}
        ],
        "last_verified_at": "2025-11-18T12:00:00Z"
    },
    "paypal": {
        "entity_id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "PayPal",
        "official_domain": "paypal.com",
        "confidence_score": 67.5,
        "risk_level": "low",
        "verification_sources": [
            {"source_type": "wikipedia", "url": "https://en.wikipedia.org/wiki/PayPal", "score": 67.5}
        ],
        "similar_domains": [
            {"domain": "paypai.com", "risk": "high", "similarity": 0.95}
        ],
        "last_verified_at": "2025-11-18T12:00:00Z"
    },
    "google": {
        "entity_id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Google",
        "official_domain": "google.com",
        "confidence_score": 100.0,
        "risk_level": "none",
        "verification_sources": [
            {"source_type": "wikipedia", "url": "https://en.wikipedia.org/wiki/Google", "score": 67.5},
            {"source_type": "appstore", "url": "https://apps.apple.com/app/google", "score": 75.0}
        ],
        "similar_domains": [],
        "last_verified_at": "2025-11-18T12:00:00Z"
    }
}

class LookupRequest(BaseModel):
    query: Optional[str] = None
    domain: Optional[str] = None

class SubmissionRequest(BaseModel):
    submitted_by: str
    entity_name: str
    domain: str
    evidence: Optional[Dict[str, Any]] = None

@app.get("/")
def root():
    return {
        "service": "Official Website Verification Platform - Demo",
        "version": "1.0.0",
        "status": "operational",
        "note": "This is a demo version with mock data. For full version, use Docker."
    }

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "demo"}

@app.post("/v1/lookup")
def lookup(request: LookupRequest):
    """Look up entity by name or domain."""
    if not request.query and not request.domain:
        raise HTTPException(status_code=400, detail="Either query or domain required")
    
    search_term = (request.query or request.domain).lower()
    
    # Search in mock data
    for key, entity in MOCK_ENTITIES.items():
        if (search_term in entity["name"].lower() or 
            search_term in entity["official_domain"].lower() or
            search_term in key):
            return {"ok": True, "data": entity}
    
    return {
        "ok": True,
        "data": None,
        "message": f"No entity found for '{search_term}'. Try: HDFC Bank, PayPal, or Google"
    }

@app.get("/v1/entities/{entity_id}")
def get_entity(entity_id: str):
    """Get entity details."""
    for entity in MOCK_ENTITIES.values():
        if entity["entity_id"] == entity_id:
            return entity
    
    raise HTTPException(status_code=404, detail="Entity not found")

@app.post("/v1/submissions")
def submit_domain(submission: SubmissionRequest):
    """Submit a domain for verification."""
    return {
        "ok": True,
        "submission_id": "550e8400-e29b-41d4-a716-446655440099",
        "status": "pending",
        "message": "Submission received! (Demo mode - not actually saved)"
    }

@app.post("/v1/domains/check")
def check_domain(request: LookupRequest):
    """Quick domain check."""
    if not request.domain:
        raise HTTPException(status_code=400, detail="Domain required")
    
    domain = request.domain.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    
    for entity in MOCK_ENTITIES.values():
        if domain in entity["official_domain"]:
            return {
                "ok": True,
                "domain": domain,
                "known": True,
                "entity_name": entity["name"],
                "confidence_score": entity["confidence_score"],
                "risk_level": entity["risk_level"]
            }
    
    return {
        "ok": True,
        "domain": domain,
        "known": False,
        "risk_level": "unknown",
        "message": "Domain not in verified database"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔒 Official Website Verification Platform - DEMO MODE")
    print("="*60)
    print("\n📍 API running at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("\n💡 Try these examples:")
    print("\n1. Search for HDFC Bank:")
    print('   curl -X POST http://localhost:8000/v1/lookup \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "HDFC Bank"}\'')
    print("\n2. Check a domain:")
    print('   curl -X POST http://localhost:8000/v1/domains/check \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"domain": "paypal.com"}\'')
    print("\n3. View API docs:")
    print("   Open http://localhost:8000/docs in your browser")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
