# Video Downloader - Network Media Extraction

A web-based tool that extracts video URLs by intercepting browser network requests, replicating the DevTools Inspect → Network → Media workflow.

## Features

- 🎥 Extracts media URLs from webpages using headless browser automation
- 🔍 Intercepts network requests to find actual video sources
- 📦 Supports .mp4, .webm, .m3u8, .ts formats
- 🔄 Optional HLS (.m3u8) to MP4 conversion via FFmpeg
- 🚀 FastAPI backend + React TypeScript frontend
- 🐳 Docker-ready with multi-stage builds
- ✅ Comprehensive test coverage

## Quick Start

### Automated Setup (Recommended)

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Docker (Easiest)

```bash
cp .env.example .env
docker-compose up --build
```

Access at: http://localhost:8000

### Manual Setup

See [SETUP.md](SETUP.md) for detailed instructions.

**Note:** TypeScript errors in the editor will disappear after running `npm install` in the frontend directory.

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Fix common issues
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy to production
- **[EDGE_CASES.md](EDGE_CASES.md)** - Limitations and edge cases

## Legal Notice

This tool only extracts media files that are publicly accessible through normal browser network requests. It does NOT bypass DRM, authentication, or any access controls. Users are responsible for complying with copyright laws and terms of service.
