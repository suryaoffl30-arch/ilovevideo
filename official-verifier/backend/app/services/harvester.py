"""Harvester service for collecting official website data from external sources."""
import httpx
import asyncio
from typing import List, Optional, Dict
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

from app.services.scoring import SIGNAL_PRESETS


async def harvest_wikidata(entity_name: str) -> List[str]:
    """
    Harvest official website URLs from Wikidata.
    
    Args:
        entity_name: Name of the entity to search
    
    Returns:
        List of official website URLs
    """
    urls = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search for entity
            search_url = "https://www.wikidata.org/w/api.php"
            search_params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": entity_name,
                "limit": 3
            }
            
            response = await client.get(search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            # Get entities
            for result in search_data.get("search", []):
                entity_id = result.get("id")
                if not entity_id:
                    continue
                
                # Get entity details
                entity_params = {
                    "action": "wbgetentities",
                    "format": "json",
                    "ids": entity_id,
                    "props": "claims"
                }
                
                entity_response = await client.get(search_url, params=entity_params)
                entity_response.raise_for_status()
                entity_data = entity_response.json()
                
                # Extract P856 (official website) claims
                entity_obj = entity_data.get("entities", {}).get(entity_id, {})
                claims = entity_obj.get("claims", {})
                
                if "P856" in claims:
                    for claim in claims["P856"]:
                        url = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
                        if url:
                            urls.append(url)
    
    except Exception as e:
        print(f"Error harvesting Wikidata: {e}")
    
    return urls


async def harvest_itunes(entity_name: str, country: str = "US") -> List[str]:
    """
    Harvest official website URLs from Apple iTunes Search API.
    
    Args:
        entity_name: Name of the entity/app to search
        country: Country code (default: US)
    
    Returns:
        List of seller/developer website URLs
    """
    urls = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            search_url = "https://itunes.apple.com/search"
            params = {
                "term": entity_name,
                "country": country,
                "entity": "software",
                "limit": 5
            }
            
            response = await client.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get("results", []):
                seller_url = result.get("sellerUrl")
                if seller_url:
                    urls.append(seller_url)
    
    except Exception as e:
        print(f"Error harvesting iTunes: {e}")
    
    return urls


async def harvest_play(entity_name: str) -> List[str]:
    """
    Harvest official website URLs from Google Play Store (best-effort scraping).
    
    Args:
        entity_name: Name of the app to search
    
    Returns:
        List of developer website URLs
    
    Note:
        This is a best-effort implementation. Google Play may block or rate-limit.
        TODO: Consider using official API or more robust scraping with proxies.
    """
    urls = []
    
    try:
        # Search Google Play
        search_query = entity_name.replace(" ", "+")
        search_url = f"https://play.google.com/store/search?q={search_query}&c=apps"
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = await client.get(search_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find app links (this is fragile and may break)
            app_links = soup.find_all('a', href=re.compile(r'/store/apps/details\?id='))
            
            for link in app_links[:3]:  # Check first 3 results
                app_url = "https://play.google.com" + link['href']
                
                # Get app details page
                app_response = await client.get(app_url, headers=headers)
                app_soup = BeautifulSoup(app_response.text, 'html.parser')
                
                # Try to find developer website link
                # TODO: This selector is fragile and needs updating based on Play Store structure
                website_links = app_soup.find_all('a', href=True)
                for wlink in website_links:
                    href = wlink['href']
                    if href.startswith('http') and 'google.com' not in href:
                        urls.append(href)
                        break
    
    except Exception as e:
        print(f"Error harvesting Play Store: {e}")
    
    return urls


def normalize_and_extract_domain(url: str) -> Optional[str]:
    """
    Extract and normalize domain from URL.
    
    Args:
        url: Full URL
    
    Returns:
        Normalized domain (e.g., 'example.com')
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    
    except Exception:
        return None


async def harvest_entity(entity_name: str) -> Dict[str, List[str]]:
    """
    Harvest official website data from all sources.
    
    Args:
        entity_name: Name of the entity
    
    Returns:
        Dictionary mapping source types to lists of URLs
    """
    # Run harvesters concurrently
    wikipedia_task = harvest_wikidata(entity_name)
    itunes_task = harvest_itunes(entity_name)
    play_task = harvest_play(entity_name)
    
    wikipedia_urls, itunes_urls, play_urls = await asyncio.gather(
        wikipedia_task, itunes_task, play_task,
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(wikipedia_urls, Exception):
        wikipedia_urls = []
    if isinstance(itunes_urls, Exception):
        itunes_urls = []
    if isinstance(play_urls, Exception):
        play_urls = []
    
    return {
        'wikipedia': wikipedia_urls,
        'appstore': itunes_urls,
        'playstore': play_urls
    }
