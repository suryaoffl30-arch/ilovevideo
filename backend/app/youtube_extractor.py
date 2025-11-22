"""
YouTube video extractor using yt-dlp
Extracts video/audio URLs from YouTube videos and Shorts
Downloads and merges video+audio streams when needed
"""
import logging
import asyncio
import json
import os
import uuid
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Extract video/audio URLs from YouTube using yt-dlp"""
    
    def __init__(self):
        self.download_dir = Path("/tmp/youtube_downloads")
        self.download_dir.mkdir(exist_ok=True)
    
    async def extract(self, url: str) -> Dict:
        """
        Extract video/audio from YouTube URL
        
        Args:
            url: YouTube watch/shorts URL
            
        Returns:
            Dict with videoUrl, audioUrl, title, thumbnail, and format info
        """
        try:
            logger.info(f"Extracting YouTube content from: {url}")
            
            # Validate YouTube URL
            if not self._is_youtube_url(url):
                return {
                    "error": "Invalid YouTube URL",
                    "status_code": 400
                }
            
            # Get video info using yt-dlp with format details
            info = await self._get_video_info_with_formats(url)
            
            if not info:
                return {
                    "error": "Could not extract video information",
                    "status_code": 404
                }
            
            # Get available formats
            formats = info.get("formats", [])
            
            # Find best video+audio combined format (usually format 22 or 18)
            # YouTube provides combined formats up to 720p (format 22) or 360p (format 18)
            best_combined = None
            for fmt in formats:
                vcodec = fmt.get("vcodec", "none")
                acodec = fmt.get("acodec", "none")
                # Must have both video and audio codecs
                if vcodec and vcodec != "none" and acodec and acodec != "none":
                    height = fmt.get("height") or 0
                    # Prefer higher quality combined formats
                    if not best_combined or height > (best_combined.get("height") or 0):
                        best_combined = fmt
                        logger.debug(f"Found combined format: {fmt.get('format_id')} - {height}p")
            
            # Find best video-only format
            best_video = None
            for fmt in formats:
                vcodec = fmt.get("vcodec", "none")
                acodec = fmt.get("acodec", "none")
                if vcodec and vcodec != "none" and (not acodec or acodec == "none"):
                    height = fmt.get("height") or 0
                    if not best_video or height > (best_video.get("height") or 0):
                        best_video = fmt
            
            # Find best audio-only format
            best_audio = None
            for fmt in formats:
                acodec = fmt.get("acodec", "none")
                vcodec = fmt.get("vcodec", "none")
                if acodec and acodec != "none" and (not vcodec or vcodec == "none"):
                    abr = fmt.get("abr") or 0
                    if not best_audio or abr > (best_audio.get("abr") or 0):
                        best_audio = fmt
            
            # Prepare result with all available options
            result = {
                "title": info.get("title", "YouTube Video"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "webpage_url": url,
                "status_code": 200
            }
            
            # Add combined format (best for direct download)
            if best_combined:
                result["video_url"] = best_combined.get("url")
                result["combined_download_url"] = best_combined.get("url")
                result["video_quality"] = f"{best_combined.get('height', '?')}p"
                result["video_format"] = best_combined.get("ext", "mp4")
                result["format_type"] = "video"
                logger.info(f"Found combined format: {result['video_quality']}")
            
            # Add separate video stream
            if best_video:
                result["video_only_url"] = best_video.get("url")
                result["video_only_quality"] = f"{best_video.get('height', '?')}p"
                # If no combined format, use video-only as primary
                if not best_combined:
                    result["video_url"] = best_video.get("url")
                    result["video_quality"] = result["video_only_quality"]
            
            # Add audio stream
            if best_audio:
                result["audio_url"] = best_audio.get("url")
                abr = best_audio.get("abr") or best_audio.get("tbr") or 0
                result["audio_quality"] = f"{abr:.0f}kbps" if abr else "Best"
            
            # If no combined format, we need to merge video+audio
            if not best_combined and (best_video or best_audio):
                result["requires_merge"] = True
                result["message"] = "High quality videos have separate video and audio streams"
                # Provide download instructions
                if best_video and best_audio:
                    result["download_note"] = "Download video and audio separately, then merge with FFmpeg or similar tool"
            
            logger.info(f"Successfully extracted YouTube video: {result['title']}")
            logger.info(f"Available formats - Combined: {bool(best_combined)}, Video: {bool(best_video)}, Audio: {bool(best_audio)}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"YouTube extraction failed: {error_msg}")
            
            # Handle specific errors
            if "Private video" in error_msg:
                return {"error": "Private video", "status_code": 403}
            elif "Video unavailable" in error_msg:
                return {"error": "Video unavailable or removed", "status_code": 404}
            elif "age-restricted" in error_msg.lower():
                return {"error": "Age-restricted content", "status_code": 403}
            elif "members-only" in error_msg.lower():
                return {"error": "Members-only content", "status_code": 403}
            else:
                return {"error": f"Extraction failed: {error_msg}", "status_code": 500}
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        import re
        patterns = [
            r'youtube\.com/watch',
            r'youtu\.be/',
            r'youtube\.com/shorts/',
            r'youtube\.com/playlist'
        ]
        return any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns)
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if URL is a playlist URL"""
        import re
        return bool(re.search(r'[?&]list=', url, re.IGNORECASE) or re.search(r'youtube\.com/playlist', url, re.IGNORECASE))
    
    async def _get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-playlist',
                '--no-warnings',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                return info
            else:
                logger.error(f"yt-dlp info error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return None
    
    async def get_playlist_info(self, url: str) -> Dict:
        """
        Get playlist information and video list
        
        Args:
            url: YouTube playlist URL or video URL with playlist parameter
            
        Returns:
            Dict with playlist title, video count, and list of videos
        """
        try:
            logger.info(f"Fetching playlist info from: {url}")
            
            if not self._is_playlist_url(url):
                return {
                    "error": "Not a playlist URL",
                    "status_code": 400
                }
            
            # Get playlist info using yt-dlp
            cmd = [
                'yt-dlp',
                '--flat-playlist',
                '--dump-json',
                '--no-warnings',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Failed to fetch playlist: {error_msg}")
                return {
                    "error": f"Failed to fetch playlist: {error_msg}",
                    "status_code": 500
                }
            
            # Parse video entries
            videos = []
            for line in stdout.decode().strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        videos.append({
                            "id": video_info.get("id"),
                            "title": video_info.get("title"),
                            "url": f"https://www.youtube.com/watch?v={video_info.get('id')}",
                            "duration": video_info.get("duration"),
                            "thumbnail": video_info.get("thumbnail"),
                            "uploader": video_info.get("uploader")
                        })
                    except json.JSONDecodeError:
                        continue
            
            if not videos:
                return {
                    "error": "No videos found in playlist",
                    "status_code": 404
                }
            
            # Get playlist title from first video's playlist info
            playlist_title = videos[0].get("uploader", "YouTube Playlist") if videos else "YouTube Playlist"
            
            result = {
                "playlist_title": playlist_title,
                "video_count": len(videos),
                "videos": videos,
                "status_code": 200
            }
            
            logger.info(f"Found {len(videos)} videos in playlist")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Playlist fetch failed: {error_msg}")
            return {
                "error": f"Playlist fetch failed: {error_msg}",
                "status_code": 500
            }
    
    async def _get_video_info_with_formats(self, url: str) -> Optional[Dict]:
        """Get video information with all available formats"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-playlist',
                '--no-warnings',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                return info
            else:
                logger.error(f"yt-dlp info error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get video info with formats: {str(e)}")
            return None
    
    async def _get_best_video_url(self, url: str) -> Optional[str]:
        """Get best quality video URL using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '-f', 'best',
                '-g',
                '--no-playlist',
                '--no-warnings',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                video_url = stdout.decode().strip()
                return video_url
            else:
                logger.error(f"yt-dlp video error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get video URL: {str(e)}")
            return None
    
    async def _get_best_audio_url(self, url: str) -> Optional[str]:
        """Get best quality audio URL using yt-dlp"""
        try:
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio',
                '-g',
                '--no-playlist',
                '--no-warnings',
                url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                audio_url = stdout.decode().strip()
                return audio_url
            else:
                logger.debug(f"yt-dlp audio error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.debug(f"Failed to get audio URL: {str(e)}")
            return None
    
    async def download_and_merge(self, url: str, quality: str = "720p", format_type: str = "video") -> Dict:
        """
        Download video and audio separately, then merge them with FFmpeg
        This is the most reliable method for YouTube videos
        """
        try:
            logger.info(f"Downloading and merging YouTube video: {url}")
            
            # Validate YouTube URL
            if not self._is_youtube_url(url):
                return {
                    "error": "Invalid YouTube URL",
                    "status_code": 400
                }
            
            # Try to update yt-dlp to latest version (helps with 403 errors)
            try:
                update_cmd = ['pip3', 'install', '--break-system-packages', '--upgrade', 'yt-dlp']
                update_process = await asyncio.create_subprocess_exec(
                    *update_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await update_process.communicate()
                logger.info("yt-dlp updated to latest version")
            except Exception as e:
                logger.warning(f"Could not update yt-dlp: {e}")
            
            # Generate unique filename
            video_id = str(uuid.uuid4())[:8]
            output_file = self.download_dir / f"youtube_{video_id}.mp4"
            
            # Use yt-dlp to download and merge automatically
            # Format selection based on requested quality and type
            
            if format_type == "audio":
                # Audio-only download with MP3 conversion
                output_file = self.download_dir / f"youtube_{video_id}.mp3"
                format_string = "bestaudio/best"
                logger.info(f"Downloading audio only (MP3)")
                
                cmd = [
                    'yt-dlp',
                    '-f', format_string,
                    '-x',  # Extract audio
                    '--audio-format', 'mp3',
                    '--audio-quality', '0',  # Best quality
                    '-o', str(output_file),
                    '--no-playlist',
                    '--no-warnings',
                    '--no-check-certificates',
                    url
                ]
            else:
                # Video download with quality selection
                quality_map = {
                    "360p": "best[height<=360][ext=mp4]/best[height<=360]/best",
                    "480p": "best[height<=480][ext=mp4]/best[height<=480]/best",
                    "720p": "best[height<=720][ext=mp4]/best[height<=720]/best",
                    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best",
                    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
                }
                
                format_string = quality_map.get(quality, quality_map["720p"])
                logger.info(f"Downloading video with quality: {quality} (format: {format_string})")
                
                cmd = [
                    'yt-dlp',
                    '-f', format_string,
                    '--merge-output-format', 'mp4',
                    '-o', str(output_file),
                    '--no-playlist',
                    '--no-warnings',
                    '--no-check-certificates',
                    url
                ]
            
            logger.info(f"Running yt-dlp command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and output_file.exists():
                # Get video info
                info = await self._get_video_info(url)
                
                file_size = output_file.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                
                result = {
                    "status": "success",
                    "title": info.get("title", "YouTube Video") if info else "YouTube Video",
                    "thumbnail": info.get("thumbnail") if info else None,
                    "duration": info.get("duration") if info else None,
                    "uploader": info.get("uploader") if info else None,
                    "file_path": str(output_file),
                    "file_size": file_size,
                    "file_size_mb": f"{file_size_mb:.2f}",
                    "download_url": f"/api/youtube/file/{output_file.name}",
                    "format_type": format_type,
                    "file_extension": "mp3" if format_type == "audio" else "mp4",
                    "status_code": 200
                }
                
                logger.info(f"Successfully downloaded and merged: {result['title']} ({result['file_size_mb']} MB)")
                return result
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"yt-dlp download failed: {error_msg}")
                
                # Handle specific errors
                if "Private video" in error_msg:
                    return {"error": "Private video", "status_code": 403}
                elif "Video unavailable" in error_msg:
                    return {"error": "Video unavailable or removed", "status_code": 404}
                elif "age-restricted" in error_msg.lower():
                    return {"error": "Age-restricted content", "status_code": 403}
                else:
                    return {"error": f"Download failed: {error_msg}", "status_code": 500}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"YouTube download and merge failed: {error_msg}")
            return {"error": f"Download failed: {error_msg}", "status_code": 500}
