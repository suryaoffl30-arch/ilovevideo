import asyncio
import os
import logging
import hashlib
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class VideoConverter:
    """Handles video conversion, primarily HLS (.m3u8) to MP4 using FFmpeg"""
    
    @staticmethod
    async def convert_hls_to_mp4(m3u8_url: str) -> Optional[str]:
        """
        Convert HLS stream (.m3u8) to MP4 file using FFmpeg
        
        Args:
            m3u8_url: URL of the .m3u8 playlist file
            
        Returns:
            Path to converted MP4 file, or None if conversion failed
        """
        if not settings.enable_ffmpeg_conversion:
            logger.info("FFmpeg conversion is disabled")
            return None
        
        try:
            # Generate unique filename
            url_hash = hashlib.md5(m3u8_url.encode()).hexdigest()[:8]
            output_file = os.path.join(settings.download_dir, f"video_{url_hash}.mp4")
            
            # Check if already converted
            if os.path.exists(output_file):
                logger.info(f"File already exists: {output_file}")
                return output_file
            
            logger.info(f"Converting HLS to MP4: {m3u8_url}")
            
            # FFmpeg command to download and convert HLS stream
            cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',  # Copy streams without re-encoding (faster)
                '-bsf:a', 'aac_adtstoasc',  # Fix AAC stream
                '-y',  # Overwrite output file
                output_file
            ]
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_file):
                logger.info(f"Conversion successful: {output_file}")
                return output_file
            else:
                logger.error(f"FFmpeg failed: {stderr.decode()}")
                return None
                
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
            return None
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return None
    
    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Check if FFmpeg is installed and available"""
        try:
            import subprocess
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
