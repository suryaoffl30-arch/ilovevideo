"""
Instagram video extractor
Extracts video URLs from Instagram reels, posts, and carousel videos
"""
import logging
import re
import json
from typing import Optional, Dict
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class InstagramExtractor:
    """Extract video URLs from Instagram content"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def extract(self, url: str) -> Dict:
        """
        Extract video from Instagram URL
        
        Args:
            url: Instagram reel/post URL
            
        Returns:
            Dict with video_url, thumbnail, dimensions, title
        """
        try:
            logger.info(f"Extracting Instagram content from: {url}")
            
            # Validate Instagram URL
            if not self._is_instagram_url(url):
                return {
                    "error": "Invalid Instagram URL",
                    "status_code": 400
                }
            
            # Fetch the page
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 404:
                    return {
                        "error": "Content not found or removed",
                        "status_code": 404
                    }
                
                if response.status_code == 403:
                    return {
                        "error": "Private content or access denied",
                        "status_code": 403
                    }
                
                html = response.text
            
            # Try multiple extraction methods
            result = self._extract_from_json(html)
            if not result:
                result = self._extract_from_meta_tags(html)
            
            if result:
                logger.info(f"Successfully extracted Instagram video")
                return {
                    "video_url": result.get("video_url"),
                    "thumbnail": result.get("thumbnail"),
                    "title": result.get("title", "Instagram Video"),
                    "dimensions": result.get("dimensions"),
                    "status_code": 200
                }
            else:
                return {
                    "error": "Could not extract video URL",
                    "status_code": 404
                }
                
        except httpx.TimeoutException:
            return {
                "error": "Request timeout",
                "status_code": 408
            }
        except Exception as e:
            logger.error(f"Instagram extraction failed: {str(e)}")
            return {
                "error": f"Extraction failed: {str(e)}",
                "status_code": 500
            }
    
    def _is_instagram_url(self, url: str) -> bool:
        """Check if URL is a valid Instagram URL"""
        patterns = [
            r'instagram\.com/p/',
            r'instagram\.com/reel/',
            r'instagram\.com/tv/',
            r'instagram\.com/reels/'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def _extract_from_json(self, html: str) -> Optional[Dict]:
        """Extract video from embedded JSON data"""
        try:
            # Try to find __additionalDataLoaded or window._sharedData
            patterns = [
                r'window\.__additionalDataLoaded\([^,]+,({.+?})\);',
                r'window\._sharedData = ({.+?});',
                r'<script type="application/ld\+json">({.+?})</script>'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        video_url = self._find_video_url_in_json(data)
                        if video_url:
                            return {
                                "video_url": video_url,
                                "thumbnail": self._find_thumbnail_in_json(data),
                                "title": self._find_title_in_json(data)
                            }
                    except:
                        continue
            
            return None
        except Exception as e:
            logger.debug(f"JSON extraction failed: {str(e)}")
            return None
    
    def _extract_from_meta_tags(self, html: str) -> Optional[Dict]:
        """Extract video from meta tags"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try og:video meta tag
            video_meta = soup.find('meta', property='og:video')
            if video_meta and video_meta.get('content'):
                video_url = video_meta['content']
                
                # Get thumbnail
                thumbnail_meta = soup.find('meta', property='og:image')
                thumbnail = thumbnail_meta['content'] if thumbnail_meta else None
                
                # Get title
                title_meta = soup.find('meta', property='og:title')
                title = title_meta['content'] if title_meta else "Instagram Video"
                
                return {
                    "video_url": video_url,
                    "thumbnail": thumbnail,
                    "title": title
                }
            
            return None
        except Exception as e:
            logger.debug(f"Meta tag extraction failed: {str(e)}")
            return None
    
    def _find_video_url_in_json(self, data: dict) -> Optional[str]:
        """Recursively find video URL in JSON data"""
        if isinstance(data, dict):
            if 'video_url' in data:
                return data['video_url']
            for value in data.values():
                result = self._find_video_url_in_json(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_video_url_in_json(item)
                if result:
                    return result
        return None
    
    def _find_thumbnail_in_json(self, data: dict) -> Optional[str]:
        """Find thumbnail URL in JSON data"""
        if isinstance(data, dict):
            if 'display_url' in data:
                return data['display_url']
            if 'thumbnail_src' in data:
                return data['thumbnail_src']
            for value in data.values():
                result = self._find_thumbnail_in_json(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_thumbnail_in_json(item)
                if result:
                    return result
        return None
    
    def _find_title_in_json(self, data: dict) -> str:
        """Find title in JSON data"""
        if isinstance(data, dict):
            if 'title' in data:
                return data['title']
            if 'edge_media_to_caption' in data:
                edges = data['edge_media_to_caption'].get('edges', [])
                if edges and len(edges) > 0:
                    return edges[0].get('node', {}).get('text', '')[:100]
        return "Instagram Video"
