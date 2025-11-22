from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import uuid
import os
import sys
import asyncio
from typing import Dict
from datetime import datetime
from pathlib import Path
import shutil

# Fix for Python 3.13 on Windows - use ProactorEventLoop for subprocess support
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.config import settings
from app.models import (
    ExtractRequest, ExtractResponse, ExtractionStatus,
    ProgressResponse, HistoryItem
)
from app.converter import VideoConverter
from app.instagram_extractor import InstagramExtractor
from app.youtube_extractor import YouTubeExtractor
from app.livestream import LivestreamManager

# Configure logging FIRST
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import extractor - prefer Playwright for full automation
try:
    # Try Playwright first (works in Docker with Python 3.11)
    from app.extractor import MediaExtractor
    logger.info("Using Playwright extractor (full browser automation)")
except Exception as e:
    logger.warning(f"Playwright not available: {e}")
    try:
        # Fallback to Selenium
        from app.extractor_selenium import SeleniumMediaExtractor as MediaExtractor
        logger.info("Using Selenium extractor")
    except ImportError:
        # Final fallback to Simple HTTP
        from app.extractor_simple import SimpleMediaExtractor as MediaExtractor
        logger.info("Using Simple HTTP extractor (limited functionality)")

# Initialize FastAPI app
app = FastAPI(
    title="Video Downloader API",
    description="Extract video URLs from webpages using network interception",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
import os
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

# Task tracking
tasks: Dict[str, Dict] = {}
history: list[HistoryItem] = []

# Livestream manager
livestream_manager = LivestreamManager()


@app.get("/api")
async def api_root():
    """API health check endpoint"""
    return {
        "status": "online",
        "message": "Video Downloader API",
        "ffmpeg_available": VideoConverter.is_ffmpeg_available()
    }


@app.get("/")
async def root():
    """Serve frontend"""
    from fastapi.responses import FileResponse
    import os
    
    index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # Fallback to API response if frontend not built
        return {
            "status": "online",
            "message": "Video Downloader API",
            "frontend": "not found - use /api endpoints",
            "ffmpeg_available": VideoConverter.is_ffmpeg_available()
        }


@app.post("/api/extract", response_model=ExtractResponse)
async def extract_video(request: ExtractRequest, background_tasks: BackgroundTasks):
    """
    Extract video URL from webpage by intercepting network requests.
    This replicates the DevTools Inspect → Network → Media workflow.
    
    If direct_url=True, treats the URL as a direct video link (no extraction needed).
    
    Args:
        request: ExtractRequest with webpage URL or direct video URL
        
    Returns:
        ExtractResponse with media URL and download link
    """
    try:
        url = str(request.url)
        logger.info(f"Extraction request for: {url} (direct={request.direct_url})")
        
        # If it's a direct video URL, skip extraction
        if request.direct_url or _is_direct_video_url(url):
            task_id = str(uuid.uuid4())
            tasks[task_id] = {
                "status": ExtractionStatus.COMPLETED,
                "progress": 100,
                "message": "Direct video URL provided",
                "url": url,
                "media_url": url,
                "download_url": url
            }
            
            # Add to history
            history.append(HistoryItem(
                url=url,
                media_url=url,
                timestamp=datetime.now().isoformat(),
                status=ExtractionStatus.COMPLETED
            ))
            
            return ExtractResponse(
                status=ExtractionStatus.COMPLETED,
                message="Direct video URL ready",
                media_url=url,
                download_url=url,
                task_id=task_id
            )
        
        # Check for DRM-protected sites (basic check)
        if _is_drm_protected(url):
            raise HTTPException(
                status_code=400,
                detail="This site uses DRM protection. Cannot extract protected content."
            )
        
        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": ExtractionStatus.LOADING,
            "progress": 0,
            "message": "Starting extraction...",
            "url": url
        }
        
        # Start extraction in background
        background_tasks.add_task(
            _extract_video_task,
            task_id,
            url,
            request.convert_hls
        )
        
        return ExtractResponse(
            status=ExtractionStatus.LOADING,
            message="Extraction started",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _extract_video_task(task_id: str, url: str, convert_hls: bool):
    """Background task for video extraction"""
    try:
        # Update progress
        tasks[task_id].update({
            "status": ExtractionStatus.EXTRACTING,
            "progress": 20,
            "message": "Loading page with headless browser..."
        })
        
        # Extract media using Playwright (async)
        extractor = MediaExtractor()
        media_files = await extractor.extract(url)
        
        if not media_files:
            tasks[task_id].update({
                "status": ExtractionStatus.FAILED,
                "progress": 100,
                "message": "No media files found on this page"
            })
            return
        
        # Handle both single file and list of files
        if not isinstance(media_files, list):
            media_files = [media_files]
        
        tasks[task_id].update({
            "progress": 60,
            "message": f"Found {len(media_files)} media file(s)"
        })
        
        # Prepare all media files for download
        media_list = []
        all_media_serializable = []
        
        for i, media_file in enumerate(media_files):
            media_info = {
                "url": media_file.url,
                "extension": media_file.extension,
                "size": media_file.size,
                "index": i
            }
            media_list.append(media_info)
            
            # Store serializable version with cookies/headers
            all_media_serializable.append({
                "url": media_file.url,
                "extension": media_file.extension,
                "size": media_file.size,
                "cookies": getattr(media_file, 'cookies', []),
                "headers": getattr(media_file, 'headers', {})
            })
        
        # Mark as completed with all media files
        tasks[task_id].update({
            "status": ExtractionStatus.COMPLETED,
            "progress": 100,
            "message": f"Extraction completed - {len(media_files)} file(s) found",
            "media_files": media_list,
            "media_url": media_files[0].url,  # Keep for backward compatibility
            "download_url": media_files[0].url,  # Keep for backward compatibility
            "cookies": getattr(media_files[0], 'cookies', []),
            "headers": getattr(media_files[0], 'headers', {}),
            "all_media": all_media_serializable  # Store serializable version
        })
        
        # Add to history
        history.append(HistoryItem(
            url=url,
            media_url=media_file.url,
            timestamp=datetime.now().isoformat(),
            status=ExtractionStatus.COMPLETED
        ))
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        tasks[task_id].update({
            "status": ExtractionStatus.FAILED,
            "progress": 100,
            "message": f"Error: {str(e)}"
        })


@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get extraction progress for a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    # Return all task data (includes playlist-specific fields)
    response = {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"],
        "download_url": task.get("download_url")
    }
    
    # Add playlist-specific fields if present
    if "total_videos" in task:
        response["total_videos"] = task["total_videos"]
        response["completed_videos"] = task["completed_videos"]
        response["failed_videos"] = task["failed_videos"]
        response["downloads"] = task.get("downloads", [])
    
    # Add other optional fields
    if "title" in task:
        response["title"] = task["title"]
    if "thumbnail" in task:
        response["thumbnail"] = task["thumbnail"]
    if "duration" in task:
        response["duration"] = task["duration"]
    if "uploader" in task:
        response["uploader"] = task["uploader"]
    if "file_size_mb" in task:
        response["file_size_mb"] = task["file_size_mb"]
    if "media_files" in task:
        response["media_files"] = task["media_files"]
    
    return response


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download converted video file"""
    file_path = os.path.join(settings.download_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename
    )


@app.get("/api/proxy-download/{task_id}/{index:int}")
@app.get("/api/proxy-download/{task_id}")
async def proxy_download(task_id: str, index: int = 0):
    """Proxy download with authentication headers"""
    from fastapi.responses import StreamingResponse
    import httpx
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    all_media = task.get("all_media", [])
    
    # Get the specific media file by index
    if not all_media or index >= len(all_media):
        raise HTTPException(status_code=404, detail="Media file not found")
    
    media_file = all_media[index]
    media_url = media_file.get("url")
    cookies = media_file.get("cookies", [])
    headers = media_file.get("headers", {})
    
    if not media_url:
        raise HTTPException(status_code=404, detail="Media URL not found")
    
    try:
        # Convert cookies to dict format
        cookie_dict = {}
        if cookies:
            for cookie in cookies:
                cookie_dict[cookie.get('name')] = cookie.get('value')
        
        # Get filename from URL
        filename = media_url.split('/')[-1].split('?')[0] or 'video.mp4'
        if not any(filename.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.m3u8']):
            filename += '.mp4'
        
        # Stream the video with authentication
        async def stream_video():
            async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
                async with client.stream('GET', media_url, headers=headers, cookies=cookie_dict) as response:
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Failed to download video: {response.status_code}"
                        )
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
        
        return StreamingResponse(
            stream_video(),
            media_type='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"Proxy download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.get("/api/history")
async def get_history():
    """Get download history"""
    return {"history": history[-10:]}  # Last 10 items


def _is_drm_protected(url: str) -> bool:
    """
    Basic check for known DRM-protected platforms.
    This is NOT comprehensive - just a safety check.
    """
    drm_domains = [
        'netflix.com',
        'disneyplus.com',
        'hulu.com',
        'hbomax.com',
        'amazon.com/prime',
        'apple.com/tv'
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in drm_domains)


def _is_direct_video_url(url: str) -> bool:
    """Check if URL is a direct video file"""
    video_extensions = ['.mp4', '.webm', '.m3u8', '.ts', '.mov', '.avi', '.mkv', '.flv']
    url_lower = url.lower()
    return any(ext in url_lower for ext in video_extensions)


@app.post("/api/instagram/download")
async def download_instagram(request: ExtractRequest, format_type: str = "video"):
    """
    Download Instagram reel/post video or audio
    
    Supports:
    - Instagram reels
    - Instagram posts with videos
    - Instagram TV (IGTV)
    - Carousel videos
    
    Format options: video (MP4), audio (MP3)
    """
    try:
        url = str(request.url)
        logger.info(f"Instagram download request: {url} (format: {format_type})")
        
        extractor = InstagramExtractor()
        result = await extractor.extract(url)
        
        status_code = result.pop("status_code", 200)
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=result.get("error"))
        
        # Add format type to result
        result["format_type"] = format_type
        
        # If audio requested, note that user needs to extract it from video
        if format_type == "audio":
            result["audio_note"] = "Download the video and extract audio using a converter, or use the YouTube audio feature for direct MP3 downloads"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Instagram download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube/download")
async def download_youtube(request: ExtractRequest, background_tasks: BackgroundTasks, quality: str = "720p", format_type: str = "video"):
    """
    Download YouTube video/audio
    
    Supports:
    - youtube.com/watch
    - youtu.be/
    - youtube.com/shorts/
    
    Quality options: 360p, 480p, 720p, 1080p, best
    Format options: video (MP4), audio (MP3)
    
    Downloads video and audio separately, then merges them with FFmpeg
    Returns task_id for progress tracking
    """
    try:
        url = str(request.url)
        format_label = "audio (MP3)" if format_type == "audio" else f"video ({quality})"
        logger.info(f"YouTube download request: {url} ({format_label})")
        
        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "downloading",
            "progress": 0,
            "message": f"Starting YouTube download ({format_label})...",
            "url": url,
            "quality": quality,
            "format_type": format_type
        }
        
        # Start download in background
        background_tasks.add_task(_youtube_download_task, task_id, url, quality, format_type)
        
        return {
            "status": "downloading",
            "message": f"YouTube download started ({format_label})",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _youtube_download_task(task_id: str, url: str, quality: str = "720p", format_type: str = "video"):
    """Background task for YouTube download"""
    try:
        format_label = "audio (MP3)" if format_type == "audio" else f"video ({quality})"
        tasks[task_id].update({
            "status": "downloading",
            "progress": 10,
            "message": f"Downloading {format_label} from YouTube..."
        })
        
        extractor = YouTubeExtractor()
        result = await extractor.download_and_merge(url, quality, format_type)
        
        if result.get("status") == "success":
            tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Download completed!",
                "title": result.get("title"),
                "thumbnail": result.get("thumbnail"),
                "duration": result.get("duration"),
                "uploader": result.get("uploader"),
                "file_size_mb": result.get("file_size_mb"),
                "download_url": result.get("download_url")
            })
        else:
            tasks[task_id].update({
                "status": "failed",
                "progress": 100,
                "message": result.get("error", "Download failed")
            })
            
    except Exception as e:
        logger.error(f"YouTube download task {task_id} failed: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}"
        })


@app.get("/api/youtube/file/{filename}")
async def get_youtube_file(filename: str):
    """Serve downloaded YouTube video file"""
    file_path = Path("/tmp/youtube_downloads") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check - ensure file is in the download directory
    if not str(file_path.resolve()).startswith("/tmp/youtube_downloads"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/youtube/playlist/info")
async def get_youtube_playlist_info(request: ExtractRequest):
    """
    Get YouTube playlist information
    
    Returns list of videos in the playlist with metadata
    """
    try:
        url = str(request.url)
        logger.info(f"Playlist info request: {url}")
        
        extractor = YouTubeExtractor()
        result = await extractor.get_playlist_info(url)
        
        status_code = result.pop("status_code", 200)
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist info error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube/playlist/download")
async def download_youtube_playlist(
    request: ExtractRequest,
    background_tasks: BackgroundTasks,
    video_ids: str = "",
    quality: str = "720p",
    format_type: str = "video"
):
    """
    Download multiple videos from YouTube playlist
    
    Parameters:
    - video_ids: Comma-separated list of video IDs to download
    - quality: Video quality (360p, 480p, 720p, 1080p, best)
    - format_type: "video" or "audio"
    """
    try:
        url = str(request.url)
        selected_ids = [vid.strip() for vid in video_ids.split(",") if vid.strip()]
        
        if not selected_ids:
            raise HTTPException(status_code=400, detail="No videos selected")
        
        logger.info(f"Playlist download request: {len(selected_ids)} videos")
        
        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "downloading",
            "progress": 0,
            "message": f"Starting playlist download ({len(selected_ids)} videos)...",
            "total_videos": len(selected_ids),
            "completed_videos": 0,
            "failed_videos": 0,
            "current_video": "",
            "downloads": []
        }
        
        # Start batch download in background
        background_tasks.add_task(
            _playlist_download_task,
            task_id,
            selected_ids,
            quality,
            format_type
        )
        
        return {
            "status": "downloading",
            "message": f"Playlist download started ({len(selected_ids)} videos)",
            "task_id": task_id,
            "total_videos": len(selected_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _playlist_download_task(
    task_id: str,
    video_ids: list,
    quality: str,
    format_type: str
):
    """Background task for playlist download"""
    extractor = YouTubeExtractor()
    total = len(video_ids)
    completed = 0
    failed = 0
    downloads = []
    
    for idx, video_id in enumerate(video_ids):
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Update progress
            tasks[task_id].update({
                "progress": int((idx / total) * 100),
                "current_video": video_id,
                "message": f"Downloading video {idx + 1}/{total}..."
            })
            
            # Download video
            result = await extractor.download_and_merge(video_url, quality, format_type)
            
            if result.get("status") == "success":
                completed += 1
                downloads.append({
                    "video_id": video_id,
                    "title": result.get("title"),
                    "download_url": result.get("download_url"),
                    "file_size_mb": result.get("file_size_mb"),
                    "status": "success"
                })
            else:
                failed += 1
                downloads.append({
                    "video_id": video_id,
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                })
            
            tasks[task_id].update({
                "completed_videos": completed,
                "failed_videos": failed,
                "downloads": downloads
            })
            
        except Exception as e:
            logger.error(f"Failed to download video {video_id}: {str(e)}")
            failed += 1
            downloads.append({
                "video_id": video_id,
                "status": "failed",
                "error": str(e)
            })
    
    # Mark as completed
    tasks[task_id].update({
        "status": "completed",
        "progress": 100,
        "message": f"Playlist download completed! {completed} successful, {failed} failed",
        "completed_videos": completed,
        "failed_videos": failed,
        "downloads": downloads
    })


@app.post("/api/convert/upload")
async def upload_video_for_conversion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a video file for audio extraction
    
    Accepts video files and converts them to MP3
    """
    try:
        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create upload directory
        upload_dir = Path("/tmp/video_uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        input_path = upload_dir / f"video_{file_id}{file_ext}"
        
        # Save uploaded file
        logger.info(f"Uploading file: {file.filename} ({file.content_type})")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = input_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        logger.info(f"File uploaded: {file_size_mb:.2f} MB")
        
        # Create task for conversion
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "uploading",
            "progress": 50,
            "message": "File uploaded, starting conversion...",
            "filename": file.filename,
            "file_size_mb": f"{file_size_mb:.2f}"
        }
        
        # Start conversion in background
        background_tasks.add_task(
            _convert_video_to_audio,
            task_id,
            str(input_path),
            file.filename
        )
        
        return {
            "status": "processing",
            "message": "File uploaded successfully, converting to MP3...",
            "task_id": task_id,
            "filename": file.filename,
            "file_size_mb": f"{file_size_mb:.2f}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _convert_video_to_audio(task_id: str, input_path: str, original_filename: str):
    """Background task for video to audio conversion"""
    try:
        tasks[task_id].update({
            "status": "converting",
            "progress": 60,
            "message": "Extracting audio from video..."
        })
        
        # Generate output filename
        output_dir = Path("/tmp/converted_audio")
        output_dir.mkdir(exist_ok=True)
        
        file_id = Path(input_path).stem
        output_path = output_dir / f"{file_id}.mp3"
        
        # Use FFmpeg to extract audio
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-q:a', '0',  # Best quality
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        logger.info(f"Converting: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0 and output_path.exists():
            file_size = output_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Conversion completed!",
                "download_url": f"/api/convert/download/{output_path.name}",
                "output_filename": output_path.name,
                "output_size_mb": f"{file_size_mb:.2f}"
            })
            
            # Clean up input file
            try:
                os.remove(input_path)
            except:
                pass
            
            logger.info(f"Conversion completed: {output_path.name} ({file_size_mb:.2f} MB)")
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"FFmpeg error: {error_msg}")
            
            tasks[task_id].update({
                "status": "failed",
                "progress": 100,
                "message": f"Conversion failed: {error_msg[:200]}"
            })
            
    except Exception as e:
        logger.error(f"Conversion task failed: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}"
        })


@app.get("/api/convert/download/{filename}")
async def download_converted_audio(filename: str):
    """Download converted MP3 file"""
    file_path = Path("/tmp/converted_audio") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check
    if not str(file_path.resolve()).startswith("/tmp/converted_audio"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/compress/upload")
async def upload_video_for_compression(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: str = "medium"
):
    """
    Upload a video file for compression
    
    Quality options:
    - high: 720p, 2000k bitrate (~60% size)
    - medium: 480p, 1000k bitrate (~40% size)
    - low: 360p, 500k bitrate (~20% size)
    """
    try:
        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate quality
        if quality not in ['high', 'medium', 'low']:
            quality = 'medium'
        
        # Create upload directory
        upload_dir = Path("/tmp/video_compress")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        input_path = upload_dir / f"video_{file_id}{file_ext}"
        
        # Save uploaded file
        logger.info(f"Uploading file for compression: {file.filename} ({file.content_type})")
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = input_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # Estimate compressed size
        size_reduction = {"high": 0.6, "medium": 0.4, "low": 0.2}
        estimated_size_mb = file_size_mb * size_reduction[quality]
        
        logger.info(f"File uploaded: {file_size_mb:.2f} MB, quality: {quality}")
        
        # Create task for compression
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "uploading",
            "progress": 50,
            "message": "File uploaded, starting compression...",
            "filename": file.filename,
            "file_size_mb": f"{file_size_mb:.2f}",
            "quality": quality,
            "estimated_size_mb": f"{estimated_size_mb:.2f}"
        }
        
        # Start compression in background
        background_tasks.add_task(
            _compress_video,
            task_id,
            str(input_path),
            file.filename,
            quality
        )
        
        return {
            "status": "processing",
            "message": f"File uploaded successfully, compressing to {quality} quality...",
            "task_id": task_id,
            "filename": file.filename,
            "file_size_mb": f"{file_size_mb:.2f}",
            "estimated_size_mb": f"{estimated_size_mb:.2f}",
            "quality": quality
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _compress_video(task_id: str, input_path: str, original_filename: str, quality: str):
    """Background task for video compression"""
    try:
        tasks[task_id].update({
            "status": "compressing",
            "progress": 60,
            "message": f"Compressing video to {quality} quality..."
        })
        
        # Generate output filename
        output_dir = Path("/tmp/compressed_video")
        output_dir.mkdir(exist_ok=True)
        
        file_id = Path(input_path).stem
        output_path = output_dir / f"{file_id}_compressed.mp4"
        
        # Compression settings based on quality
        settings = {
            "high": {
                "scale": "1280:720",  # 720p
                "bitrate": "2000k",
                "description": "720p, 2MB/s"
            },
            "medium": {
                "scale": "854:480",  # 480p
                "bitrate": "1000k",
                "description": "480p, 1MB/s"
            },
            "low": {
                "scale": "640:360",  # 360p
                "bitrate": "500k",
                "description": "360p, 500KB/s"
            }
        }
        
        config = settings.get(quality, settings["medium"])
        
        # Use FFmpeg to compress video
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"scale={config['scale']}:force_original_aspect_ratio=decrease,pad={config['scale']}:(ow-iw)/2:(oh-ih)/2",
            '-c:v', 'libx264',
            '-b:v', config['bitrate'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-preset', 'medium',
            '-y',
            str(output_path)
        ]
        
        logger.info(f"Compressing: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0 and output_path.exists():
            file_size = output_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            # Calculate compression ratio
            original_size = Path(input_path).stat().st_size / (1024 * 1024)
            compression_ratio = ((original_size - file_size_mb) / original_size) * 100
            
            tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"Compression completed! ({compression_ratio:.1f}% size reduction)",
                "download_url": f"/api/compress/download/{output_path.name}",
                "output_filename": output_path.name,
                "output_size_mb": f"{file_size_mb:.2f}",
                "compression_ratio": f"{compression_ratio:.1f}",
                "quality_description": config['description']
            })
            
            # Clean up input file
            try:
                os.remove(input_path)
            except:
                pass
            
            logger.info(f"Compression completed: {output_path.name} ({file_size_mb:.2f} MB, {compression_ratio:.1f}% reduction)")
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"FFmpeg error: {error_msg}")
            
            tasks[task_id].update({
                "status": "failed",
                "progress": 100,
                "message": f"Compression failed: {error_msg[:200]}"
            })
            
    except Exception as e:
        logger.error(f"Compression task failed: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}"
        })


@app.get("/api/compress/download/{filename}")
async def download_compressed_video(filename: str):
    """Download compressed video file"""
    file_path = Path("/tmp/compressed_video") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check
    if not str(file_path.resolve()).startswith("/tmp/compressed_video"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/live/status")
async def check_livestream_status(request: ExtractRequest):
    """
    Check YouTube livestream status
    
    Returns:
    - live_now: Stream is currently live
    - upcoming: Stream is scheduled but not started
    - ended_and_archived: Stream ended and video is available
    - not_live: Not a livestream or unavailable
    """
    try:
        url = str(request.url)
        logger.info(f"Livestream status check: {url}")
        
        result = await livestream_manager.check_stream_status(url)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Livestream status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/live/start-recording")
async def start_livestream_recording(request: ExtractRequest):
    """
    Start recording a live YouTube stream
    
    Returns recording ID and process info
    """
    try:
        url = str(request.url)
        logger.info(f"Start recording request: {url}")
        
        # Check if stream is live
        status_result = await livestream_manager.check_stream_status(url)
        
        if status_result.get("status") != "live_now":
            raise HTTPException(
                status_code=400,
                detail=f"Stream is not live. Status: {status_result.get('status')}"
            )
        
        # Generate recording ID
        recording_id = str(uuid.uuid4())
        
        # Start recording
        result = await livestream_manager.start_recording(url, recording_id)
        
        if not result.get("recording"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start recording error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/live/stop-recording/{recording_id}")
async def stop_livestream_recording(recording_id: str):
    """
    Stop an active livestream recording
    
    Returns file info and download URL
    """
    try:
        logger.info(f"Stop recording request: {recording_id}")
        
        result = await livestream_manager.stop_recording(recording_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stop recording error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/live/recording-status/{recording_id}")
async def get_recording_status(recording_id: str):
    """
    Get status of an active recording
    
    Returns recording progress and file size
    """
    try:
        result = await livestream_manager.get_recording_status(recording_id)
        
        if not result.get("found"):
            raise HTTPException(status_code=404, detail="Recording not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recording status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/live/download-archive")
async def download_archived_stream(request: ExtractRequest, background_tasks: BackgroundTasks):
    """
    Download an archived (ended) livestream
    
    Returns download URL when complete
    """
    try:
        url = str(request.url)
        logger.info(f"Archive download request: {url}")
        
        # Check if stream is archived
        status_result = await livestream_manager.check_stream_status(url)
        
        if status_result.get("status") not in ["ended_and_archived", "not_live"]:
            raise HTTPException(
                status_code=400,
                detail=f"Stream is not archived. Status: {status_result.get('status')}"
            )
        
        # Create task for download
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "downloading",
            "progress": 0,
            "message": "Downloading archived livestream..."
        }
        
        # Start download in background
        background_tasks.add_task(_download_archive_task, task_id, url)
        
        return {
            "status": "downloading",
            "message": "Archive download started",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Archive download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _download_archive_task(task_id: str, url: str):
    """Background task for archive download"""
    try:
        tasks[task_id].update({
            "progress": 50,
            "message": "Downloading archived stream..."
        })
        
        result = await livestream_manager.download_archive(url)
        
        if result.get("archived"):
            tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Archive downloaded!",
                "download_url": result.get("download_url"),
                "filename": result.get("filename"),
                "file_size_mb": result.get("file_size_mb")
            })
        else:
            tasks[task_id].update({
                "status": "failed",
                "progress": 100,
                "message": f"Download failed: {result.get('error')}"
            })
            
    except Exception as e:
        logger.error(f"Archive download task failed: {str(e)}")
        tasks[task_id].update({
            "status": "failed",
            "progress": 100,
            "message": f"Error: {str(e)}"
        })


@app.get("/api/live/download/{filename}")
async def download_livestream_file(filename: str):
    """Download recorded livestream file"""
    file_path = Path("/tmp/livestream_downloads") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Security check
    if not str(file_path.resolve()).startswith("/tmp/livestream_downloads"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/live/cleanup")
async def cleanup_old_recordings(days: int = 7):
    """
    Delete recordings older than specified days
    
    Default: 7 days
    """
    try:
        deleted_count = livestream_manager.cleanup_old_recordings(days)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} old recordings"
        }
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)
