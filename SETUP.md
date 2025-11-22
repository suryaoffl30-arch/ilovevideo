# Setup Instructions

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Git

## Quick Setup

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install:
- react & react-dom
- axios
- TypeScript types
- Vite
- Testing libraries

#### 2. Install Backend Dependencies

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

#### 3. Configure Environment

```bash
# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env if needed (defaults should work for local development)
```

#### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
# Make sure venv is activated
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

## Docker Setup (Easiest)

If you have Docker installed:

```bash
# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Build and run
docker-compose up --build
```

Access at: http://localhost:8000

## Troubleshooting

### TypeScript Errors in Editor

If you see TypeScript errors in your editor:

1. Make sure you've run `npm install` in the frontend directory
2. Restart your editor/IDE
3. In VS Code: Press Ctrl+Shift+P → "TypeScript: Restart TS Server"

### Playwright Installation Issues

```bash
# Install with dependencies
playwright install chromium --with-deps

# Or install system dependencies separately
playwright install-deps
```

### FFmpeg Not Found

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract and add to PATH

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### Port Already in Use

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

## Verify Installation

### Check Backend

```bash
cd backend
python -c "import fastapi; import playwright; print('Backend dependencies OK')"
```

### Check Frontend

```bash
cd frontend
npm run build
```

Should complete without errors.

### Check FFmpeg

```bash
ffmpeg -version
```

Should show FFmpeg version info.

## Next Steps

Once setup is complete:

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand how it works
2. Read [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
3. Read [EDGE_CASES.md](EDGE_CASES.md) for limitations
4. Try extracting a video from a test site

## Test the Application

Try these test URLs:

1. **Simple MP4:**
   ```
   https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4
   ```

2. **HLS Stream:**
   ```
   https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8
   ```

## Development Tips

### Hot Reload

Both frontend and backend support hot reload:
- Frontend: Vite automatically reloads on file changes
- Backend: `--reload` flag enables auto-restart

### Running Tests

**Backend:**
```bash
cd backend
pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm run test
```

### Debugging

**Backend:**
Set `DEBUG=true` in .env for verbose logging

**Frontend:**
Open browser DevTools (F12) to see console logs and network requests

## IDE Setup

### VS Code (Recommended)

Install these extensions:
- Python
- Pylance
- ESLint
- Prettier
- TypeScript Vue Plugin (Volar)

### PyCharm

1. Mark `backend` as Sources Root
2. Set Python interpreter to the venv
3. Enable TypeScript support

## Common Issues

### "Module not found" errors

**Solution:** Run `npm install` in frontend directory

### "playwright not found"

**Solution:** 
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
playwright install chromium
```

### TypeScript errors in App.tsx

**Solution:** These will disappear after running `npm install`. The errors occur because React types aren't installed yet.

### CORS errors

**Solution:** Check that `CORS_ORIGINS` in .env includes your frontend URL

## Getting Help

If you encounter issues:

1. Check this SETUP.md file
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment-specific issues
3. Check [EDGE_CASES.md](EDGE_CASES.md) for known limitations
4. Check the logs for error messages
5. Open an issue on GitHub with:
   - Your OS and versions (Node, Python)
   - Exact error message
   - Steps to reproduce
