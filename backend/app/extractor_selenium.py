"""
Alternative extractor using Selenium WebDriver instead of Playwright.
This works around Python 3.13 + Windows + Playwright subprocess issues.
"""
import logging
import time
import re
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import os
import glob
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse

from app.models import MediaFile, ExtractionStatus
from app.config import settings

logger = logging.getLogger(__name__)


class SeleniumMediaExtractor:
    """
    Extracts media URLs using Selenium WebDriver with Chrome DevTools Protocol.
    Works on Python 3.13 + Windows without subprocess issues.
    """
    
    MEDIA_EXTENSIONS = {'.mp4', '.webm', '.m3u8', '.ts', '.mov', '.avi', '.mkv', '.flv'}
    
    MEDIA_MIME_TYPES = {
        'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime',
        'application/vnd.apple.mpegurl', 'application/x-mpegurl',
        'video/mp2t', 'application/octet-stream'
    }
    
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
        self.network_logs = []
        
    def extract(self, url: str) -> Optional[MediaFile]:
        """
        Extract media URLs using Selenium + Chrome DevTools
        
        Args:
            url: Webpage URL to extract media from
            
        Returns:
            MediaFile object with extracted media URL, or None if not found
        """
        self.status = ExtractionStatus.LOADING
        self.captured_media = []
        
        # Setup Edge options
        edge_options = Options()
        edge_options.add_argument('--headless')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--window-size=1920,1080')
        edge_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Enable performance logging to capture network requests
        edge_options.set_capability('ms:loggingPrefs', {'performance': 'ALL'})
        
        driver = None
        try:
            logger.info(f"Loading page: {url}")
            self.status = ExtractionStatus.EXTRACTING
            
            # Try to find msedgedriver.exe in common locations
            driver_path = None
            possible_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedgedriver.exe",
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Microsoft', 'Edge', 'Application', 'msedgedriver.exe'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Microsoft', 'Edge', 'Application', 'msedgedriver.exe'),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    driver_path = path
                    logger.info(f"Found EdgeDriver at: {path}")
                    break
            
            # Create Edge driver
            if driver_path:
                service = Service(driver_path)
                driver = webdriver.Edge(service=service, options=edge_options)
            else:
                # Try without specifying driver path (assumes it's in PATH)
                logger.info("EdgeDriver not found in common locations, trying system PATH")
                driver = webdriver.Edge(options=edge_options)
            driver.set_page_load_timeout(settings.playwright_timeout / 1000)
            
            # Navigate to page
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get performance logs (network requests)
            logs = driver.get_log('performance')
            
            # Parse logs for media URLs
            for entry in logs:
                try:
                    log = entry['message']
                    if 'Network.responseReceived' in log or 'Network.requestWillBeSent' in log:
                        import json
                        log_data = json.loads(log)
                        
                        if 'message' in log_data:
                            message = log_data['message']
                            params = message.get('params', {})
                            
                            # Get URL from request or response
                            request_url = None
                            content_type = None
                            
                            if 'request' in params:
                                request_url = params['request'].get('url')
                            elif 'response' in params:
                                response = params['response']
                                request_url = response.get('url')
                                content_type = response.get('mimeType', '')
                                if not content_type:
                                    headers = response.get('headers', {})
                                    content_type = headers.get('content-type', headers.get('Content-Type', ''))
                            
                            if request_url and self._is_media_url(request_url, content_type):
                                if not self._should_exclude(request_url):
                                    # Extract extension
                                    extension = self._get_extension(request_url, content_type)
                                    
                                    media_file = MediaFile(
                                        url=request_url,
                                        type=content_type or 'unknown',
                                        extension=extension
                                    )
                                    
                                    # Avoid duplicates
                                    if not any(m.url == request_url for m in self.captured_media):
                                        self.captured_media.append(media_file)
                                        logger.info(f"Captured media: {request_url[:100]}...")
                except Exception as e:
                    logger.debug(f"Error parsing log entry: {e}")
                    continue
            
            if self.captured_media:
                logger.info(f"Found {len(self.captured_media)} media files")
                return self.captured_media[0]
            else:
                logger.warning("No media files found")
                return None
                
        except TimeoutException:
            logger.error("Page load timeout")
            self.status = ExtractionStatus.FAILED
            return None
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            self.status = ExtractionStatus.FAILED
            raise
        finally:
            if driver:
                driver.quit()
    
    def _is_media_url(self, url: str, content_type: str = None) -> bool:
        """Check if URL or content type indicates media"""
        url_lower = url.lower()
        
        # Check URL extension
        if any(ext in url_lower for ext in self.MEDIA_EXTENSIONS):
            return True
        
        # Check content type
        if content_type:
            content_type_lower = content_type.lower()
            if any(mime in content_type_lower for mime in self.MEDIA_MIME_TYPES):
                return True
        
        return False
    
    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded (ads, trackers, etc.)"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in self.EXCLUDE_PATTERNS)
    
    def _get_extension(self, url: str, content_type: str = None) -> str:
        """Extract file extension from URL or content type"""
        url_lower = url.lower()
        
        for ext in self.MEDIA_EXTENSIONS:
            if ext in url_lower:
                return ext
        
        # Guess from content type
        if content_type:
            content_type_lower = content_type.lower()
            if 'mp4' in content_type_lower:
                return '.mp4'
            elif 'webm' in content_type_lower:
                return '.webm'
            elif 'm3u8' in content_type_lower or 'mpegurl' in content_type_lower:
                return '.m3u8'
        
        return '.mp4'  # default
