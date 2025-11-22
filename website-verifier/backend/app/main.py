"""FastAPI backend for website verification service."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
from verifier import WebsiteVerifier

app = FastAPI(title="Website Verifier API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

verifier = WebsiteVerifier()

class VerifyRequest(BaseModel):
    url: str

class SearchRequest(BaseModel):
    name: str

@app.get("/")
def root():
    return {"message": "Website Verifier API", "version": "1.0"}

@app.post("/api/verify")
def verify_website(request: VerifyRequest):
    """Verify if a URL is official and safe."""
    try:
        result = verifier.verify_url(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/search")
def search_website(request: SearchRequest):
    """Search for official websites by name."""
    results = verifier.search_by_name(request.name)
    return {"results": results, "count": len(results)}

@app.get("/api/redirect/{domain:path}")
def safe_redirect(domain: str):
    """API endpoint for safe redirects - returns official URL."""
    result = verifier.verify_url(f"https://{domain}")
    if result["verified"]:
        return {"redirect_to": result["official_url"], "safe": True}
    elif result["official_url"]:
        return {
            "redirect_to": result["official_url"],
            "safe": False,
            "warning": result["warning"]
        }
    else:
        raise HTTPException(status_code=404, detail="Domain not found in database")
