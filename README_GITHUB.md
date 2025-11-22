# 🎥 Video Downloader - Complete Media Extraction Platform

A powerful web-based video downloader that automates browser DevTools network interception to extract and download videos from any website, with specialized support for YouTube and Instagram.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## ✨ Features

### 🌐 General Website Support
- Extract videos from any website using Playwright network interception
- Captures all media files (.mp4, .webm, .m3u8, .ts)
- Authenticated downloads with cookie/header capture
- Multi-file download support

### 📷 Instagram Integration
- Download Instagram Reels
- Download Instagram Posts with videos
- Support for IGTV and carousel videos
- Format selector (Video/Audio)

### ▶️ YouTube Features
- **Single Video Downloads** with quality selector (360p-1080p)
- **Audio Extraction** (MP3 format)
- **Playlist Downloads** with selective video picking
- **Livestream Recording** (record live streams in real-time)
- **Archive Downloads** (download ended livestreams)
- Progress tracking for all operations

### 🎵 Media Conversion
- **Video to MP3** converter (upload any video, get audio)
- **Video Compression** with quality presets (High/Medium/Low)
- FFmpeg-powered processing

### 🚀 Advanced Features
- Real-time progress tracking
- Multi-file capture and download
- Background task processing
- Authenticated proxy downloads
- Auto-play detection for videos

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11)
- **Playwright** (Browser automation)
- **yt-dlp** (YouTube extraction)
- **FFmpeg** (Media processing)
- **httpx** (Async HTTP client)

### Frontend
- **React 18** (TypeScript)
- **Vite** (Build tool)
- **Axios** (API client)
- **CSS3** (Responsive design)

### DevOps
- **Docker** (Containerization)
- **Docker Compose** (Orchestration)
- **Gunicorn** (Production server)
- **NGINX** (Reverse proxy)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/video-downloader.git
cd video-downloader

# Start application
docker-compose up -d --build

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

### Development Mode

```bash
# Backend (in Docker)
docker-compose up -d

# Frontend (local)
cd frontend
npm install
npm run dev
```

## 📖 Usage

### 1. General Website Video Download
1. Paste webpage URL
2. Click "Extract Video"
3. Wait for extraction
4. Download video(s)

### 2. Instagram Download
1. Paste Instagram Reel/Post URL
2. Select format (Video/Audio)
3. Click "📷 Instagram"
4. Download

### 3. YouTube Download
1. Paste YouTube URL
2. Select format (Video/MP3)
3. Select quality (360p-1080p)
4. Click "▶️ YouTube"
5. Download

### 4. YouTube Playlist
1. Paste playlist URL
2. Review video list
3. Select videos to download
4. Click "📥 Download X Videos"
5. Download each video

### 5. Livestream Recording
1. Click "🔴 Livestream Recorder"
2. Paste livestream URL
3. Click "Check Status"
4. If live: Click "⏺️ Start Recording"
5. Click "⏹️ Stop Recording" when done
6. Download recording

### 6. Video to MP3
1. Click "🎵 Convert Video to MP3"
2. Upload video file
3. Click "🎵 Convert to MP3"
4. Download MP3

### 7. Video Compression
1. Click "🗜️ Compress Video"
2. Select quality (High/Medium/Low)
3. Upload video file
4. Click "🗜️ Compress Video"
5. Download compressed video

## 📁 Project Structure

```
video-downloader/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── extractor.py         # Playwright network interception
│   │   ├── youtube_extractor.py # YouTube-specific extraction
│   │   ├── instagram_extractor.py # Instagram extraction
│   │   ├── livestream.py        # Livestream recording
│   │   ├── converter.py         # FFmpeg video conversion
│   │   ├── models.py            # Pydantic models
│   │   └── config.py            # Configuration
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main React component
│   │   ├── api.ts               # API client
│   │   ├── App.css              # Styles
│   │   └── main.tsx             # Entry point
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml           # Development
├── docker-compose.prod.yml      # Production
├── Dockerfile                   # Development
├── Dockerfile.prod              # Production
├── nginx.prod.conf              # NGINX configuration
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create `.env` file:

```bash
# Application
DEBUG=false
WORKERS=4
LOG_LEVEL=info

# Limits
MAX_DOWNLOAD_SIZE=500MB
MAX_RECORDING_TIME=7200
CLEANUP_DAYS=1

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 🚀 Deployment

### Option 1: DigitalOcean (Recommended)
See [DIGITALOCEAN_DEPLOYMENT.md](DIGITALOCEAN_DEPLOYMENT.md)

### Option 2: AWS
See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

### Option 3: Render.com (Free)
See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

### Production Deployment
See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

## 📊 API Documentation

### Endpoints

#### General Extraction
- `POST /api/extract` - Extract video from any website
- `GET /api/progress/{task_id}` - Get extraction progress
- `GET /api/proxy-download/{task_id}/{index}` - Download with authentication

#### Instagram
- `POST /api/instagram/download` - Download Instagram video

#### YouTube
- `POST /api/youtube/download` - Download YouTube video/audio
- `POST /api/youtube/playlist/info` - Get playlist information
- `POST /api/youtube/playlist/download` - Download playlist videos

#### Livestream
- `POST /api/live/status` - Check livestream status
- `POST /api/live/start-recording` - Start recording live stream
- `POST /api/live/stop-recording/{id}` - Stop recording
- `GET /api/live/recording-status/{id}` - Get recording status
- `POST /api/live/download-archive` - Download archived stream

#### Conversion
- `POST /api/convert/upload` - Upload video for MP3 conversion
- `POST /api/compress/upload` - Upload video for compression

Full API documentation: [API.md](API.md)

## 🧪 Testing

```bash
# Backend tests
docker exec video-downloader pytest

# Frontend tests
cd frontend
npm test
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Notice

This tool is for educational purposes and personal use only. Users are responsible for:
- Respecting copyright laws
- Following platform Terms of Service
- Not downloading DRM-protected content
- Obtaining necessary permissions

**Do not use for:**
- Downloading copyrighted content without permission
- Violating platform Terms of Service
- Commercial redistribution
- DRM circumvention

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube extraction
- [Playwright](https://playwright.dev/) - Browser automation
- [FFmpeg](https://ffmpeg.org/) - Media processing
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [FAQ.md](FAQ.md)

## 🗺️ Roadmap

- [ ] User authentication
- [ ] Download history with database
- [ ] Batch operations
- [ ] Video editing features
- [ ] Mobile app (React Native)
- [ ] Browser extension
- [ ] API rate limiting
- [ ] Premium features

---

**Made with ❤️ by [Your Name]**

**Star ⭐ this repo if you find it useful!**
