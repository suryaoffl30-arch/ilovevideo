"""
Simple extractor that works without browser automation.
Uses HTTP requests to fetch page and extract video URLs from HTML/JavaScript.
"""
import logging
import re
import requests
from typing import Optional, List
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from app.models import MediaFile, ExtractionStatus
from app.config import settings

logger = logging.getLogger(__name__)


class SimpleMediaExtractor:
    """
    Extracts media URLs from HTML and JavaScript without browser automation.
    Works offline and doesn't require Selenium/Playwright.
    """
    
    MEDIA_EXTENSIONS = {'.mp4', '.webm', '.m3u8', '.ts', '.mov', '.avi', '.mkv', '.flv'}
    
    EXCLUDE_PATTERNS = [
        r'doubleclick\.net',
        r'googlesyndication',
        r'analytics',
        r'tracking',
        r'pixel',
        r'beacon',
        r'ad[sv]?\.', 
        r'advertisement'
    ]
    
    def __init__(self):
        self.captured_media: List[MediaFile] = []
        self.status = ExtractionStatus.PENDING
        
    def extract(self, url: str) -> Optional[MediaFile]:
        """
        Extract media URLs from page HTML and JavaScript
        
        Args:
            url: Webpage URL to extract media from
            
        Returns:
            MediaFile object with extracted media URL, or None if not found
        """
        self.status = ExtractionStatus.LOADING
        self.captured_media = []
        
        try:
            logger.info(f"Fetching page: {url}")
            self.status = ExtractionStatus.EXTRACTING
            
            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Find video/source tags
            video_tags = soup.find_all(['video', 'source'])
            for tag in video_tags:
                src = tag.get('src') or tag.get('data-src')
                if src:
                    full_url = urljoin(url, src)
                    if self._is_media_url(full_url) and not self._should_exclude(full_url):
                        self._add_media(full_url)
            
            # Method 2: Find URLs in JavaScript/JSON
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for URLs in JavaScript
                    urls = re.findall(r'https?://[^\s<>"\']+\.(?:mp4|webm|m3u8|ts|mov)', script.string, re.IGNORECASE)
                    for found_url in urls:
                        # Clean up URL (remove trailing characters)
                        found_url = re.sub(r'["\',;}\]]+$', '', found_url)
                        if not self._should_exclude(found_url):
                            self._add_media(found_url)
            
            # Method 3: Search entire HTML for video URLs
            all_urls = re.findall(r'https?://[^\s<>"\']+\.(?:mp4|webm|m3u8|ts|mov)', html_content, re.IGNORECASE)
            for found_url in all_urls:
                found_url = re.sub(r'["\',;}\]]+$', '', found_url)
                if not self._should_exclude(found_url):
                    self._add_media(found_url)
            
            if self.captured_media:
                logger.info(f"Found {len(self.captured_media)} media files")
                return self.captured_media[0]
            else:
                logger.warning("No media files found")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            self.status = ExtractionStatus.FAILED
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            self.status = ExtractionStatus.FAILED
            raise
    
    def _add_media(self, url: str):
        """Add media URL to captured list (avoid duplicates)"""
        if not any(m.url == url for m in self.captured_media):
            extension = self._get_extension(url)
            media_file = MediaFile(
                url=url,
                type='video',
                extension=extension
            )
            self.captured_media.append(media_file)
            logger.info(f"Captured media: {url[:100]}...")
    
    def _is_media_url(self, url: str) -> bool:
        """Check if URL points to a media file"""
        url_lower = url.lower()
        return any(ext in url_lower for ext in self.MEDIA_EXTENSIONS)
    
    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded (ads, trackers, etc.)"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in self.EXCLUDE_PATTERNS)
    
    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        url_lower = url.lower()
        
        for ext in self.MEDIA_EXTENSIONS:
            if ext in url_lower:
                return ext
        
        return '.mp4'  # default
