#!/bin/bash

echo "========================================"
echo "Video Downloader - Setup Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo -e "${RED}✗ Node.js is not installed${NC}"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}✗ Python 3 is not installed${NC}"; exit 1; }
echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Frontend setup
echo "[1/5] Setting up frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: npm install failed${NC}"
        exit 1
    fi
else
    echo "Frontend dependencies already installed"
fi
cd ..

# Backend setup
echo ""
echo "[2/5] Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Failed to create virtual environment${NC}"
        exit 1
    fi
else
    echo "Virtual environment already exists"
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python packages..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: pip install failed${NC}"
    exit 1
fi

echo "Installing Playwright browsers..."
playwright install chromium
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Playwright installation failed${NC}"
    exit 1
fi

cd ..

# Environment file
echo ""
echo "[3/5] Setting up environment file..."
if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
else
    echo ".env file already exists"
fi

# Downloads directory
echo ""
echo "[4/5] Creating downloads directory..."
mkdir -p downloads

# Verify installation
echo ""
echo "[5/5] Verifying installation..."
cd backend
source venv/bin/activate
python -c "import fastapi; import playwright; print('✓ Backend dependencies OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Backend verification failed${NC}"
else
    echo -e "${GREEN}✓ Backend dependencies OK${NC}"
fi
cd ..

cd frontend
npm run build > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Frontend build failed${NC}"
else
    echo -e "${GREEN}✓ Frontend build OK${NC}"
fi
cd ..

# Check FFmpeg
command -v ffmpeg >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ FFmpeg is installed${NC}"
else
    echo -e "${RED}✗ FFmpeg is not installed (optional but recommended)${NC}"
    echo "  Install with: sudo apt install ffmpeg (Ubuntu) or brew install ffmpeg (Mac)"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
echo "========================================"
