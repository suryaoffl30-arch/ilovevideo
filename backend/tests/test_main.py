import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.models import MediaFile, ExtractionStatus

client = TestClient(app)


def test_health_check():
    """Test the root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_extract_drm_protected_url():
    """Test that DRM-protected URLs return 400 error"""
    response = client.post(
        "/api/extract",
        json={"url": "https://netflix.com/watch/12345"}
    )
    assert response.status_code == 400
    assert "DRM" in response.json()["detail"]


def test_extract_unsupported_site():
    """Test that unsupported sites return clear error"""
    with patch('app.main._extract_video_task') as mock_task:
        response = client.post(
            "/api/extract",
            json={"url": "https://example.com/video"}
        )
        assert response.status_code == 200
        assert "task_id" in response.json()


@pytest.mark.asyncio
async def test_extractor_no_media_found():
    """Test extraction when no media files are found"""
    from app.extractor import MediaExtractor
    
    with patch.object(MediaExtractor, 'extract', return_value=None):
        extractor = MediaExtractor()
        result = await extractor.extract("https://example.com")
        assert result is None


@pytest.mark.asyncio
async def test_extractor_media_found():
    """Test successful media extraction"""
    from app.extractor import MediaExtractor
    
    mock_media = MediaFile(
        url="https://example.com/video.mp4",
        type="video/mp4",
        extension=".mp4"
    )
    
    with patch.object(MediaExtractor, 'extract', return_value=mock_media):
        extractor = MediaExtractor()
        result = await extractor.extract("https://example.com")
        assert result is not None
        assert result.extension == ".mp4"


def test_progress_endpoint_not_found():
    """Test progress endpoint with invalid task ID"""
    response = client.get("/api/progress/invalid-task-id")
    assert response.status_code == 404


def test_download_file_not_found():
    """Test download endpoint with non-existent file"""
    response = client.get("/api/download/nonexistent.mp4")
    assert response.status_code == 404


def test_history_endpoint():
    """Test history endpoint returns list"""
    response = client.get("/api/history")
    assert response.status_code == 200
    assert "history" in response.json()
    assert isinstance(response.json()["history"], list)


def test_extract_invalid_url():
    """Test extraction with invalid URL format"""
    response = client.post(
        "/api/extract",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_media_url_filtering():
    """Test that media URL filtering works correctly"""
    from app.extractor import MediaExtractor
    
    extractor = MediaExtractor()
    
    # Test valid media URLs
    assert extractor._is_media_url("https://example.com/video.mp4")
    assert extractor._is_media_url("https://example.com/stream.m3u8")
    assert extractor._is_media_url("https://example.com/video.webm")
    
    # Test invalid URLs
    assert not extractor._is_media_url("https://example.com/page.html")
    assert not extractor._is_media_url("https://example.com/image.jpg")


@pytest.mark.asyncio
async def test_exclude_patterns():
    """Test that ad/tracker URLs are excluded"""
    from app.extractor import MediaExtractor
    
    extractor = MediaExtractor()
    
    # Should exclude ads
    assert extractor._should_exclude("https://doubleclick.net/ad.mp4")
    assert extractor._should_exclude("https://googlesyndication.com/video.mp4")
    assert extractor._should_exclude("https://analytics.example.com/track.mp4")
    
    # Should not exclude legitimate URLs
    assert not extractor._should_exclude("https://example.com/video.mp4")
