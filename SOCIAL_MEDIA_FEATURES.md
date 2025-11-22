# Instagram & YouTube Download Features

## ✅ Features Implemented

### 1. Instagram Video Download
- **Endpoint:** `POST /api/instagram/download`
- **Supports:**
  - Instagram Reels
  - Instagram Posts with videos
  - Instagram TV (IGTV)
  - Carousel videos
  - Public content (no login required)

**Request:**
```json
{
  "url": "https://www.instagram.com/reel/..."
}
```

**Response:**
```json
{
  "video_url": "https://...",
  "thumbnail": "https://...",
  "title": "Instagram Video",
  "dimensions": {"width": 1080, "height": 1920},
  "status_code": 200
}
```

**Error Codes:**
- `400` - Invalid Instagram URL
- `403` - Private video or access denied
- `404` - Content not found or removed
- `500` - Extraction failed

### 2. YouTube Video Download
- **Endpoint:** `POST /api/youtube/download`
- **Supports:**
  - youtube.com/watch
  - youtu.be/
  - youtube.com/shorts/
  - Best quality video + audio extraction

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response:**
```json
{
  "video_url": "https://...",
  "audio_url": "https://...",
  "combined_download_url": "https://...",
  "title": "Video Title",
  "thumbnail": "https://...",
  "duration": 180,
  "uploader": "Channel Name",
  "status_code": 200
}
```

**Error Codes:**
- `400` - Invalid YouTube URL
- `403` - Private video, age-restricted, or members-only
- `404` - Video unavailable or removed
- `500` - Extraction failed

## 🎨 Frontend Features

### New UI Elements:
1. **Instagram Button** (📷 Instagram)
   - Gradient purple/pink Instagram colors
   - Extracts Instagram reels/posts
   
2. **YouTube Button** (▶️ YouTube)
   - Red YouTube branding
   - Extracts YouTube videos/shorts

### Display Features:
- Video thumbnail preview
- Video title
- Multiple download options:
  - Download Video
  - Download Audio (YouTube only)
  - Download Best Quality

## 🐳 Docker Updates

### New Dependencies:
- `yt-dlp` - YouTube downloader
- `beautifulsoup4` - HTML parsing for Instagram
- `ffmpeg` - Already included

### Dockerfile Changes:
```dockerfile
# Install yt-dlp globally
RUN pip3 install --break-system-packages yt-dlp
```

## 📝 Usage Examples

### Instagram:
1. Copy Instagram reel/post URL
2. Paste in the input field
3. Click "📷 Instagram" button
4. Wait for extraction
5. Click "Download Video"

### YouTube:
1. Copy YouTube video/shorts URL
2. Paste in the input field
3. Click "▶️ YouTube" button
4. Wait for extraction
5. Choose download option:
   - Video only
   - Audio only
   - Best quality (video+audio)

## 🔒 Limitations

### Instagram:
- Only works with public content
- Private accounts return 403 error
- Some videos may be protected by Instagram
- Extraction depends on Instagram's HTML structure

### YouTube:
- Age-restricted content may fail
- Members-only content returns 403
- Private videos return 403
- Live streams may not work
- Very long videos may timeout

## 🧪 Testing

### Test Instagram:
```bash
curl -X POST http://localhost:8000/api/instagram/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/..."}'
```

### Test YouTube:
```bash
curl -X POST http://localhost:8000/api/youtube/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=..."}'
```

## 🚀 Deployment

The features are fully integrated into the existing Docker setup:
1. Build: `docker-compose up --build`
2. Access: http://localhost:3000
3. Use the Instagram/YouTube buttons

## 📊 Architecture

```
User Input (IG/YT URL)
    ↓
Frontend (React)
    ↓
FastAPI Backend
    ↓
Instagram Extractor OR YouTube Extractor (yt-dlp)
    ↓
Extract Video/Audio URLs
    ↓
Return to Frontend
    ↓
User Downloads
```

## 🔧 Troubleshooting

### yt-dlp not found:
```bash
docker-compose build --no-cache
```

### Instagram extraction fails:
- Check if content is public
- Try copying URL from browser
- Instagram may have changed their HTML structure

### YouTube extraction fails:
- Check if video is available
- Try a different video
- Update yt-dlp: `pip install -U yt-dlp`

## 📈 Future Enhancements

- [ ] TikTok support
- [ ] Twitter/X video support
- [ ] Facebook video support
- [ ] Batch download multiple URLs
- [ ] Quality selection (720p, 1080p, 4K)
- [ ] Subtitle download
- [ ] Playlist support
