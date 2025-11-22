import asyncio
import re
import logging
import sys
from typing import Optional, List, Dict
from playwright.async_api import async_playwright, Page, Route, Request
from urllib.parse import urlparse, urljoin
from app.models import MediaFile, ExtractionStatus
from app.config import settings

# Fix for Python 3.13 on Windows - must be set before any async operations
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except:
        pass

logger = logging.getLogger(__name__)


class MediaExtractor:
    """
    Extracts media URLs by intercepting browser network requests.
    Replicates DevTools Inspect → Network → Media workflow.
    """
    
    # Media file extensions to capture
    MEDIA_EXTENSIONS = {'.mp4', '.webm', '.m3u8', '.ts', '.mov', '.avi', '.mkv', '.flv'}
    
    # Media MIME types to capture
    MEDIA_MIME_TYPES = {
        'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime',
        'application/vnd.apple.mpegurl', 'application/x-mpegurl',
        'video/mp2t', 'application/octet-stream'
    }
    
    # Patterns to exclude (ads, trackers, etc.)
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
        self.cookies = []
        self.headers = {}
        
    async def extract(self, url: str) -> Optional[MediaFile]:
        """
        Main extraction method - launches headless browser and captures media requests
        
        Args:
            url: Webpage URL to extract media from
            
        Returns:
            MediaFile object with extracted media URL, or None if not found
        """
        self.status = ExtractionStatus.LOADING
        self.captured_media = []
        
        async with async_playwright() as p:
            try:
                # Launch headless browser
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                # Set up network request interception
                page.on('request', self._handle_request)
                page.on('response', self._handle_response)
                
                logger.info(f"Loading page: {url}")
                self.status = ExtractionStatus.EXTRACTING
                
                # Navigate to page with longer timeout and less strict wait condition
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                except Exception as e:
                    logger.warning(f"Page load warning: {str(e)}, continuing anyway...")
                    # Continue even if page doesn't fully load
                
                # Wait a bit more for lazy-loaded videos
                await asyncio.sleep(3)
                
                # Try to trigger video load by scrolling
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                
                # Try to find and click video/play button to trigger media loading
                try:
                    logger.info("Attempting to auto-play video...")
                    
                    # Method 1: Try to play all video elements via JavaScript
                    await page.evaluate('''
                        () => {
                            const videos = document.querySelectorAll('video');
                            videos.forEach(video => {
                                try {
                                    video.muted = true; // Mute to avoid autoplay restrictions
                                    video.play();
                                    console.log('Video play triggered');
                                } catch (e) {
                                    console.log('Could not play video:', e);
                                }
                            });
                        }
                    ''')
                    await asyncio.sleep(3)
                    
                    # Method 2: Click on video elements
                    video_elements = await page.query_selector_all('video')
                    if video_elements:
                        logger.info(f"Found {len(video_elements)} video element(s)")
                        for video in video_elements:
                            try:
                                await video.click(timeout=2000)
                                logger.info("Clicked video element")
                                await asyncio.sleep(2)
                            except:
                                pass
                    
                    # Method 3: Try common play button selectors
                    play_button_selectors = [
                        'button[aria-label*="play" i]',
                        'button[aria-label*="Play" i]',
                        '[aria-label*="play" i]',
                        'button.play',
                        'button.play-button',
                        '.play-button',
                        '.play-btn',
                        '[class*="play-button"]',
                        '[class*="playButton"]',
                        '[class*="PlayButton"]',
                        'button[title*="play" i]',
                        '.video-play-button',
                        '[data-testid*="play"]',
                        'button svg[class*="play"]',
                        'div[role="button"][aria-label*="play" i]',
                    ]
                    
                    for selector in play_button_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                for element in elements[:3]:  # Try first 3 matches
                                    try:
                                        await element.click(timeout=2000)
                                        logger.info(f"Clicked play button: {selector}")
                                        await asyncio.sleep(3)
                                        break
                                    except:
                                        continue
                        except:
                            continue
                    
                    # Method 4: Try clicking anywhere on the page (some players start on any click)
                    try:
                        await page.mouse.click(500, 300)
                        logger.info("Clicked center of page")
                        await asyncio.sleep(2)
                    except:
                        pass
                    
                    logger.info("Auto-play attempts completed")
                    
                except Exception as e:
                    logger.debug(f"Auto-play error: {str(e)}")
                    # Continue anyway, some videos might already be loading
                
                # Capture cookies and headers for authenticated downloads
                self.cookies = await context.cookies()
                
                # Get common headers from the page
                self.headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': url,
                    'Origin': urlparse(url).scheme + '://' + urlparse(url).netloc,
                }
                
                await browser.close()
                
                # Return ALL valid media files found
                if self.captured_media:
                    logger.info(f"Found {len(self.captured_media)} media files")
                    
                    # Sort by size (largest first) to prioritize actual videos over thumbnails
                    sorted_media = sorted(
                        self.captured_media,
                        key=lambda x: x.size if x.size else 0,
                        reverse=True
                    )
                    
                    # Log all found media for debugging
                    for i, media in enumerate(sorted_media):
                        size_mb = media.size / (1024 * 1024) if media.size else 0
                        logger.info(f"  {i+1}. {media.url[:80]}... (size: {size_mb:.2f} MB, type: {media.extension})")
                    
                    # Store cookies and headers with ALL media files
                    for media_file in sorted_media:
                        media_file.cookies = self.cookies
                        media_file.headers = self.headers
                    
                    # Return all media files
                    return sorted_media
                else:
                    logger.warning("No media files found")
                    return None
                    
            except Exception as e:
                logger.error(f"Extraction failed: {str(e)}")
                self.status = ExtractionStatus.FAILED
                raise
    
    def _handle_request(self, request: Request):
        """Handle outgoing network requests"""
        url = request.url
        
        # Check if this is a media request
        if self._is_media_url(url):
            logger.debug(f"Media request detected: {url}")
    
    async def _handle_response(self, response):
        """Handle incoming network responses - this is where we capture media URLs"""
        try:
            url = response.url
            content_type = response.headers.get('content-type', '').lower()
            
            # Skip if already captured
            if any(m.url == url for m in self.captured_media):
                return
            
            # Skip images explicitly
            if any(img_type in content_type for img_type in ['image/', 'jpeg', 'jpg', 'png', 'gif', 'webp', 'svg']):
                return
            
            # Skip if URL looks like an image
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico']):
                return
            
            # Check if this is a media file
            if self._is_media_url(url) or self._is_media_content_type(content_type):
                # Exclude ads and trackers
                if self._should_exclude(url):
                    logger.debug(f"Excluding URL: {url}")
                    return
                
                # Extract file extension
                parsed = urlparse(url)
                path = parsed.path.lower()
                extension = None
                
                for ext in self.MEDIA_EXTENSIONS:
                    if ext in path:
                        extension = ext
                        break
                
                if not extension:
                    # Guess from content type
                    if 'mp4' in content_type:
                        extension = '.mp4'
                    elif 'webm' in content_type:
                        extension = '.webm'
                    elif 'm3u8' in content_type or 'mpegurl' in content_type:
                        extension = '.m3u8'
                    else:
                        extension = '.mp4'  # default
                
                # Get content length to prioritize larger files (actual videos)
                content_length = response.headers.get('content-length')
                size = int(content_length) if content_length else 0
                
                media_file = MediaFile(
                    url=url,
                    type=content_type,
                    extension=extension,
                    size=size
                )
                
                self.captured_media.append(media_file)
                logger.info(f"Captured media: {url[:100]}... ({content_type}, size: {size} bytes)")
                
        except Exception as e:
            logger.error(f"Error handling response: {str(e)}")
    
    def _is_media_url(self, url: str) -> bool:
        """Check if URL points to a media file based on extension"""
        url_lower = url.lower()
        return any(ext in url_lower for ext in self.MEDIA_EXTENSIONS)
    
    def _is_media_content_type(self, content_type: str) -> bool:
        """Check if content type is a media type"""
        return any(mime in content_type for mime in self.MEDIA_MIME_TYPES)
    
    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded (ads, trackers, etc.)"""
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in self.EXCLUDE_PATTERNS)
