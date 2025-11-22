# System Architecture

## Overview

This video downloader system extracts media URLs by programmatically replicating the browser DevTools "Inspect → Network → Media" workflow using headless browser automation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (React + TypeScript + Vite)                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ URL Input    │  │ Progress Bar │  │ Download Btn │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                           │  │
│  │  • POST /api/extract    - Start extraction              │  │
│  │  • GET  /api/progress   - Check progress                │  │
│  │  • GET  /api/download   - Download file                 │  │
│  │  • GET  /api/history    - Get history                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MediaExtractor (Playwright)                            │  │
│  │  • Launch headless Chromium                             │  │
│  │  • Intercept network requests                           │  │
│  │  • Filter media files                                   │  │
│  │  • Extract URLs                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VideoConverter (FFmpeg)                                │  │
│  │  • Convert HLS (.m3u8) to MP4                          │  │
│  │  • Handle video transcoding                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FILE SYSTEM                                │
│                    (downloads/ directory)                       │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + TypeScript + Vite)

**Purpose:** User interface for video extraction

**Key Features:**
- URL input with validation
- Real-time progress tracking via polling
- Download button for extracted videos
- History of recent downloads
- Responsive design

**Technology Stack:**
- React 18 with TypeScript
- Vite for fast builds
- Axios for API calls
- CSS3 for styling

**API Integration:**
```typescript
// Environment-based API URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// Polling mechanism for progress
setInterval(() => getProgress(taskId), 1000)
```

### 2. Backend (FastAPI)

**Purpose:** REST API server and orchestration layer

**Key Features:**
- RESTful API endpoints
- Background task processing
- Progress tracking
- File serving
- CORS configuration
- Input validation (Pydantic)

**Technology Stack:**
- FastAPI (async Python web framework)
- Pydantic for data validation
- Uvicorn ASGI server

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/extract` | Start video extraction |
| GET | `/api/progress/{task_id}` | Get extraction progress |
| GET | `/api/download/{filename}` | Download converted file |
| GET | `/api/history` | Get download history |

### 3. MediaExtractor (Playwright)

**Purpose:** Headless browser automation for network interception

**How It Works:**

1. **Launch Browser:**
   ```python
   browser = await playwright.chromium.launch(headless=True)
   ```

2. **Set Up Interception:**
   ```python
   page.on('request', handle_request)
   page.on('response', handle_response)
   ```

3. **Navigate to Page:**
   ```python
   await page.goto(url, wait_until='networkidle')
   ```

4. **Capture Media Requests:**
   - Monitor all network responses
   - Filter by MIME type (video/mp4, application/x-mpegurl, etc.)
   - Filter by extension (.mp4, .m3u8, .webm, .ts)
   - Exclude ads/trackers using regex patterns

5. **Extract URL:**
   - Return first valid media URL found
   - Include metadata (type, size, extension)

**Filtering Logic:**

```python
MEDIA_EXTENSIONS = {'.mp4', '.webm', '.m3u8', '.ts', '.mov'}
MEDIA_MIME_TYPES = {'video/mp4', 'video/webm', 'application/vnd.apple.mpegurl'}
EXCLUDE_PATTERNS = [r'doubleclick\.net', r'analytics', r'ad[sv]?\.']
```

### 4. VideoConverter (FFmpeg)

**Purpose:** Convert HLS streams to downloadable MP4 files

**How It Works:**

1. **Detect HLS Stream:**
   - Check if extracted URL ends with .m3u8

2. **Download and Convert:**
   ```bash
   ffmpeg -i https://example.com/video.m3u8 \
          -c copy \
          -bsf:a aac_adtstoasc \
          output.mp4
   ```

3. **Serve File:**
   - Save to downloads directory
   - Return download URL to frontend

**Why FFmpeg?**
- HLS (.m3u8) is a playlist format, not a video file
- FFmpeg downloads all segments and merges them
- `-c copy` avoids re-encoding (faster)

## Data Flow

### Extraction Flow

```
1. User enters URL
   ↓
2. Frontend sends POST /api/extract
   ↓
3. Backend creates task_id
   ↓
4. Background task starts
   ↓
5. Playwright launches browser
   ↓
6. Browser loads page
   ↓
7. Network requests intercepted
   ↓
8. Media URLs filtered and captured
   ↓
9. First valid URL extracted
   ↓
10. If .m3u8: FFmpeg converts to MP4
   ↓
11. Task marked as completed
   ↓
12. Frontend polls progress
   ↓
13. Download URL returned
   ↓
14. User downloads file
```

### Network Interception Details

**What Gets Captured:**

```
Browser Network Tab:
┌─────────────────────────────────────────┐
│ Name          Type        Size          │
├─────────────────────────────────────────┤
│ page.html     document    45 KB         │
│ style.css     stylesheet  12 KB         │
│ script.js     script      89 KB         │
│ video.mp4     video       15 MB  ← THIS │
│ ad.mp4        video       2 MB   ← SKIP │
│ analytics.js  script      5 KB          │
└─────────────────────────────────────────┘
```

**Playwright Captures:**
- Every HTTP request/response
- Headers (Content-Type, Content-Length)
- URLs
- Status codes

**Our Filter:**
- ✅ Keep: video/mp4, .m3u8, .webm
- ❌ Skip: ads, analytics, trackers

## Security Architecture

### Input Validation

```python
class ExtractRequest(BaseModel):
    url: HttpUrl  # Pydantic validates URL format
    convert_hls: bool = True
```

### DRM Protection Check

```python
def _is_drm_protected(url: str) -> bool:
    drm_domains = ['netflix.com', 'disneyplus.com', 'hulu.com']
    return any(domain in url.lower() for domain in drm_domains)
```

### CORS Configuration

```python
allow_origins = settings.cors_origins_list  # From environment
allow_credentials = True
allow_methods = ["*"]
```

### File Size Limits

```python
MAX_VIDEO_SIZE_MB = 500  # Configurable
```

## Scalability Considerations

### Current Architecture (Single Instance)

```
User → FastAPI → Playwright → FFmpeg → File
```

**Limitations:**
- One extraction at a time per instance
- Memory intensive (headless browser)
- CPU intensive (FFmpeg conversion)

### Scaled Architecture (Production)

```
                    ┌─────────────┐
Users ──────────────│ Load        │
                    │ Balancer    │
                    └─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌────────┐        ┌────────┐        ┌────────┐
   │FastAPI │        │FastAPI │        │FastAPI │
   │Instance│        │Instance│        │Instance│
   └────────┘        └────────┘        └────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    ┌─────────────┐
                    │   Redis     │
                    │ Task Queue  │
                    └─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   ┌────────┐        ┌────────┐        ┌────────┐
   │ Worker │        │ Worker │        │ Worker │
   │Playwright│      │Playwright│      │Playwright│
   └────────┘        └────────┘        └────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                    ┌─────────────┐
                    │   S3/CDN    │
                    │   Storage   │
                    └─────────────┘
```

**Improvements:**
- Horizontal scaling with multiple workers
- Task queue (Redis + Celery)
- Distributed file storage (S3)
- CDN for file delivery
- Database for persistent history

## Technology Choices

### Why Playwright over Selenium?

- ✅ Modern, actively maintained
- ✅ Better network interception API
- ✅ Faster execution
- ✅ Built-in async support
- ✅ Better documentation

### Why FastAPI over Flask/Django?

- ✅ Native async support (crucial for Playwright)
- ✅ Automatic API documentation (OpenAPI)
- ✅ Type hints and validation (Pydantic)
- ✅ High performance (comparable to Node.js)
- ✅ Modern Python features

### Why React over Vue/Angular?

- ✅ Large ecosystem
- ✅ TypeScript support
- ✅ Component reusability
- ✅ Virtual DOM performance
- ✅ Industry standard

### Why Vite over Webpack?

- ✅ Extremely fast HMR
- ✅ Optimized builds
- ✅ Simple configuration
- ✅ Native ES modules
- ✅ Better developer experience

## Performance Metrics

**Typical Extraction Times:**

| Site Type | Time | Notes |
|-----------|------|-------|
| Simple video page | 5-10s | Direct .mp4 link |
| YouTube-like | 10-20s | Complex player |
| HLS stream | 30-60s | Includes conversion |
| Heavy JavaScript | 20-30s | Slow page load |

**Resource Usage:**

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| FastAPI | Low | 50-100 MB | Minimal |
| Playwright | Medium | 200-500 MB | Minimal |
| FFmpeg | High | 100-300 MB | Temp files |

## Limitations

1. **DRM-Protected Content:** Cannot extract (by design)
2. **Authentication Required:** Cannot access logged-in content
3. **Dynamic Loading:** May miss lazy-loaded videos
4. **Rate Limiting:** Some sites may block automated access
5. **JavaScript-Heavy Sites:** May require longer timeouts
6. **Large Files:** Limited by MAX_VIDEO_SIZE_MB setting

## Future Enhancements

1. **Queue System:** Redis + Celery for background processing
2. **Database:** PostgreSQL for persistent storage
3. **Authentication:** User accounts and API keys
4. **Rate Limiting:** Prevent abuse
5. **Caching:** Cache extracted URLs
6. **Batch Processing:** Extract multiple URLs
7. **Browser Pool:** Reuse browser instances
8. **Progress Streaming:** WebSocket for real-time updates
9. **Cloud Storage:** S3 integration
10. **Analytics:** Track usage metrics
