from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from enum import Enum


class ExtractionStatus(str, Enum):
    """Status of video extraction process"""
    PENDING = "pending"
    LOADING = "loading"
    EXTRACTING = "extracting"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractRequest(BaseModel):
    """Request model for video extraction"""
    url: HttpUrl = Field(..., description="Webpage URL containing video OR direct video URL")
    convert_hls: bool = Field(default=True, description="Convert HLS to MP4")
    direct_url: bool = Field(default=False, description="True if URL is direct video link from Network tab")


class MediaFile(BaseModel):
    """Extracted media file information"""
    url: str
    type: str
    size: Optional[int] = None
    extension: str
    cookies: Optional[list] = None
    headers: Optional[dict] = None
    
    class Config:
        arbitrary_types_allowed = True


class ExtractResponse(BaseModel):
    """Response model for video extraction"""
    status: ExtractionStatus
    message: str
    media_url: Optional[str] = None
    download_url: Optional[str] = None
    media_type: Optional[str] = None
    task_id: Optional[str] = None


class ProgressResponse(BaseModel):
    """Progress tracking response"""
    task_id: str
    status: ExtractionStatus
    progress: int = Field(ge=0, le=100)
    message: str
    download_url: Optional[str] = None


class HistoryItem(BaseModel):
    """Download history item"""
    url: str
    media_url: str
    timestamp: str
    status: ExtractionStatus
