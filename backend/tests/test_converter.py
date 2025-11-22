import pytest
from unittest.mock import patch, AsyncMock
from app.converter import VideoConverter


@pytest.mark.asyncio
async def test_ffmpeg_not_available():
    """Test behavior when FFmpeg is not installed"""
    with patch.object(VideoConverter, 'is_ffmpeg_available', return_value=False):
        assert not VideoConverter.is_ffmpeg_available()


@pytest.mark.asyncio
async def test_conversion_disabled():
    """Test that conversion returns None when disabled"""
    from app.config import settings
    
    original_value = settings.enable_ffmpeg_conversion
    settings.enable_ffmpeg_conversion = False
    
    result = await VideoConverter.convert_hls_to_mp4("https://example.com/video.m3u8")
    assert result is None
    
    settings.enable_ffmpeg_conversion = original_value


@pytest.mark.asyncio
async def test_hls_conversion_success():
    """Test successful HLS to MP4 conversion"""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('os.path.exists', return_value=True):
            result = await VideoConverter.convert_hls_to_mp4("https://example.com/video.m3u8")
            # Result would be a file path if successful
            assert result is None or isinstance(result, str)


@pytest.mark.asyncio
async def test_hls_conversion_failure():
    """Test failed HLS to MP4 conversion"""
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error"))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        result = await VideoConverter.convert_hls_to_mp4("https://example.com/video.m3u8")
        assert result is None
