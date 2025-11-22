"""Website verification service to detect official sites and prevent scams."""
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
import difflib

class WebsiteVerifier:
    def __init__(self, verified_db_path: str = "verified_sites.json"):
        self.verified_db_path = verified_db_path
        self.verified_sites = self._load_verified_sites()
    
    def _load_verified_sites(self) -> Dict:
        """Load verified websites database."""
        try:
            with open(self.verified_db_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"sites": []}
    
    def verify_url(self, url: str) -> Dict:
        """Verify if URL is official and safe."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        
        # Check exact match
        for site in self.verified_sites.get("sites", []):
            if domain == site["domain"]:
                return {
                    "verified": True,
                    "official_url": site["official_url"],
                    "name": site["name"],
                    "confidence": 100,
                    "warning": None
                }
        
        # Check for similar domains (potential scams)
        similar = self._find_similar_domains(domain)
        if similar:
            return {
                "verified": False,
                "official_url": similar["official_url"],
                "name": similar["name"],
                "confidence": 0,
                "warning": f"Potential scam! Did you mean {similar['domain']}?"
            }
        
        return {
            "verified": False,
            "official_url": None,
            "name": None,
            "confidence": 0,
            "warning": "Domain not in verified database"
        }
    
    def _find_similar_domains(self, domain: str) -> Optional[Dict]:
        """Find similar domains that might indicate typosquatting."""
        for site in self.verified_sites.get("sites", []):
            similarity = difflib.SequenceMatcher(None, domain, site["domain"]).ratio()
            if similarity > 0.8:  # 80% similar
                return site
        return None
    
    def search_by_name(self, name: str) -> List[Dict]:
        """Search for official sites by company/service name."""
        results = []
        name_lower = name.lower()
        for site in self.verified_sites.get("sites", []):
            if name_lower in site["name"].lower():
                results.append({
                    "name": site["name"],
                    "official_url": site["official_url"],
                    "domain": site["domain"],
                    "category": site.get("category", "general")
                })
        return results
