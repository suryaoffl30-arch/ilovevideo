# Troubleshooting Guide

## TypeScript Errors in App.tsx

### Problem
You see errors like:
- "Cannot find module 'react'"
- "JSX element implicitly has type 'any'"
- "Property 'env' does not exist on type 'ImportMeta'"

### Cause
These errors appear because npm packages haven't been installed yet. The TypeScript compiler can't find the React type definitions.

### Solution

**Step 1: Install Dependencies**
```bash
cd frontend
npm install
```

**Step 2: Restart TypeScript Server**

If using VS Code:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "TypeScript: Restart TS Server"
3. Press Enter

If using another editor:
- Restart your IDE/editor

**Step 3: Verify**
The errors should disappear. If not:
```bash
# Clean install
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### What Gets Installed

The `npm install` command installs:
- `react` and `react-dom` - React library
- `@types/react` and `@types/react-dom` - TypeScript definitions
- `axios` - HTTP client
- `vite` - Build tool
- `typescript` - TypeScript compiler
- Testing libraries

---

## Backend Import Errors

### Problem
```
ModuleNotFoundError: No module named 'fastapi'
```

### Solution
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

---

## Playwright Not Found

### Problem
```
playwright._impl._api_types.Error: Executable doesn't exist
```

### Solution
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
playwright install chromium
playwright install-deps
```

### If Still Failing

**Linux:**
```bash
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

**Windows:**
- Run as Administrator
- Ensure Windows Defender isn't blocking

---

## FFmpeg Not Found

### Problem
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

### Solution

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH:
   - Search "Environment Variables" in Start Menu
   - Edit "Path" variable
   - Add new entry: `C:\ffmpeg\bin`
   - Restart terminal

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

**Verify:**
```bash
ffmpeg -version
```

### Workaround
If you can't install FFmpeg, disable HLS conversion:
```bash
# In .env file
ENABLE_FFMPEG_CONVERSION=false
```

Users will get the .m3u8 URL directly (can play in VLC).

---

## Port Already in Use

### Problem
```
ERROR: [Errno 48] Address already in use
```

### Solution

**Windows:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual number)
taskkill /PID 12345 /F
```

**Linux/Mac:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --port 8001
```

---

## CORS Errors

### Problem
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

### Solution

**Check .env file:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**If using different port:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:YOUR_PORT
```

**Restart backend after changing .env**

---

## Docker Build Fails

### Problem
```
ERROR: failed to solve: process "/bin/sh -c npm ci" did not complete successfully
```

### Solution

**Clear Docker cache:**
```bash
docker system prune -a
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

**Check disk space:**
```bash
df -h  # Linux/Mac
```

**Increase Docker memory:**
- Docker Desktop → Settings → Resources
- Increase Memory to at least 4GB

---

## No Media Found

### Problem
Backend returns: "No media files found on this page"

### Possible Causes & Solutions

**1. Video requires login**
- Solution: Tool doesn't support authenticated content

**2. DRM-protected content**
- Solution: Tool blocks DRM by design (Netflix, Disney+, etc.)

**3. Lazy-loaded video**
- Solution: Increase timeout in .env:
  ```bash
  PLAYWRIGHT_TIMEOUT=60000
  ```

**4. Video in iframe from different domain**
- Solution: Try the direct iframe URL instead

**5. Blob URL**
- Solution: Not currently supported

**Debug steps:**
1. Open the URL in your browser
2. Open DevTools (F12)
3. Go to Network tab
4. Filter by "Media"
5. Reload page
6. Check if you see .mp4, .m3u8, or .webm files
7. If you don't see any, the tool won't find them either

---

## HLS Conversion Fails

### Problem
```
Conversion failed: FFmpeg error
```

### Solutions

**1. Check FFmpeg is installed:**
```bash
ffmpeg -version
```

**2. Check if HLS is encrypted:**
- Encrypted HLS (AES-128) won't convert
- Solution: Disable conversion, use VLC to play .m3u8

**3. Network issues:**
- HLS segments might be unreachable
- Solution: Try again or use original URL

**4. Disable conversion:**
```bash
# In .env
ENABLE_FFMPEG_CONVERSION=false
```

---

## Memory Issues

### Problem
```
MemoryError: Unable to allocate array
```
or
```
Killed (process ran out of memory)
```

### Solutions

**1. Increase system memory**

**2. Limit video size:**
```bash
# In .env
MAX_VIDEO_SIZE_MB=200
```

**3. Close other applications**

**4. Use Docker with memory limits:**
```yaml
# In docker-compose.yml
services:
  video-downloader:
    mem_limit: 2g
```

**5. Don't run multiple extractions simultaneously**

---

## Slow Extraction

### Problem
Extraction takes more than 1 minute

### Solutions

**1. Increase timeout:**
```bash
# In .env
PLAYWRIGHT_TIMEOUT=90000
```

**2. Check internet speed:**
```bash
# Test download speed
curl -o /dev/null http://speedtest.wdc01.softlayer.com/downloads/test10.zip
```

**3. Try direct video URL:**
- Instead of page URL, use direct .mp4 URL if known

**4. Disable HLS conversion:**
```bash
ENABLE_FFMPEG_CONVERSION=false
```

---

## Tests Failing

### Backend Tests

**Problem:**
```
ImportError: cannot import name 'app' from 'app.main'
```

**Solution:**
```bash
cd backend
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

### Frontend Tests

**Problem:**
```
Error: Cannot find module '@testing-library/react'
```

**Solution:**
```bash
cd frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom
npm run test
```

---

## Environment Variables Not Loading

### Problem
Changes to .env file don't take effect

### Solution

**1. Restart the application:**
```bash
# Stop with Ctrl+C, then restart
uvicorn app.main:app --reload
```

**2. Check .env location:**
- Should be in project root (same level as docker-compose.yml)
- NOT in backend/ or frontend/ directories

**3. Check .env syntax:**
```bash
# Correct
APP_PORT=8000

# Wrong (no spaces around =)
APP_PORT = 8000
```

**4. Docker requires rebuild:**
```bash
docker-compose down
docker-compose up --build
```

---

## Windows-Specific Issues

### PowerShell Execution Policy

**Problem:**
```
cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Long Path Issues

**Problem:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solution:**
Enable long paths in Windows:
1. Run `gpedit.msc`
2. Navigate to: Computer Configuration → Administrative Templates → System → Filesystem
3. Enable "Enable Win32 long paths"
4. Restart

### Antivirus Blocking

**Problem:**
Playwright or FFmpeg blocked by antivirus

**Solution:**
- Add exception for Python and Node.js
- Temporarily disable antivirus during installation

---

## Getting More Help

### Enable Debug Logging

**Backend:**
```bash
# In .env
DEBUG=true
```

**Frontend:**
Open browser DevTools (F12) → Console tab

### Check Logs

**Docker:**
```bash
docker-compose logs -f video-downloader
```

**Local:**
Check terminal output where you ran uvicorn

### Report Issue

If none of these solutions work, open a GitHub issue with:

1. **Your environment:**
   - OS and version
   - Node.js version: `node --version`
   - Python version: `python --version`
   - Docker version (if using): `docker --version`

2. **Exact error message:**
   - Copy full error from terminal
   - Include stack trace

3. **Steps to reproduce:**
   - What commands did you run?
   - What URL did you try?

4. **What you've tried:**
   - List solutions you've attempted

5. **Logs:**
   - Backend logs
   - Browser console logs (F12)

---

## Quick Diagnostic Commands

Run these to check your setup:

```bash
# Check Node.js
node --version

# Check Python
python --version

# Check npm packages
cd frontend && npm list --depth=0

# Check Python packages
cd backend && source venv/bin/activate && pip list

# Check Playwright
cd backend && source venv/bin/activate && playwright --version

# Check FFmpeg
ffmpeg -version

# Check ports
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows

# Test backend
curl http://localhost:8000

# Test frontend build
cd frontend && npm run build
```

---

## Prevention Tips

1. **Always activate venv before running Python commands**
2. **Run `npm install` after pulling new code**
3. **Restart services after changing .env**
4. **Use setup scripts for clean installation**
5. **Keep dependencies updated:**
   ```bash
   cd frontend && npm update
   cd backend && pip install --upgrade -r requirements.txt
   ```
