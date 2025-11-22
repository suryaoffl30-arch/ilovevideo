@echo off
echo ========================================
echo Video Downloader - Setup Script
echo ========================================
echo.

echo [1/5] Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages...
    call npm install
    if errorlevel 1 (
        echo ERROR: npm install failed
        exit /b 1
    )
) else (
    echo Frontend dependencies already installed
)
cd ..

echo.
echo [2/5] Setting up backend...
cd backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
) else (
    echo Virtual environment already exists
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed
    exit /b 1
)

echo Installing Playwright browsers...
playwright install chromium
if errorlevel 1 (
    echo ERROR: Playwright installation failed
    exit /b 1
)

cd ..

echo.
echo [3/5] Setting up environment file...
if not exist .env (
    echo Copying .env.example to .env...
    copy .env.example .env
) else (
    echo .env file already exists
)

echo.
echo [4/5] Creating downloads directory...
if not exist downloads mkdir downloads

echo.
echo [5/5] Verifying installation...
cd backend
call venv\Scripts\activate.bat
python -c "import fastapi; import playwright; print('✓ Backend dependencies OK')"
cd ..

cd frontend
call npm run build > nul 2>&1
if errorlevel 1 (
    echo ✗ Frontend build failed
) else (
    echo ✓ Frontend build OK
)
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo Terminal 1 - Backend:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn app.main:app --reload
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Or use Docker:
echo   docker-compose up --build
echo.
echo ========================================
pause
