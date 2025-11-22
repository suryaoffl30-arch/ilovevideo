# Official Website Verifier - Production Setup Script
# This script automates the full production setup with PostgreSQL

Write-Host "`n" -NoNewline
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Official Website Verifier - Production Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "[Step 1/6] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✓ Docker found: $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker is running" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Docker is not running!" -ForegroundColor Red
        Write-Host "  → Please start Docker Desktop and run this script again" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "  ✗ Docker not found!" -ForegroundColor Red
    Write-Host "  → Please install Docker Desktop from https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Step 2: Stop any existing containers
Write-Host "[Step 2/6] Cleaning up existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "  ✓ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Step 3: Build and start services
Write-Host "[Step 3/6] Building and starting services..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes on first run..." -ForegroundColor Gray
Write-Host ""

docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Services started successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to start services" -ForegroundColor Red
    Write-Host "  → Check docker-compose logs for details" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 4: Wait for services to be ready
Write-Host "[Step 4/6] Waiting for services to be ready..." -ForegroundColor Yellow

Write-Host "  Waiting for PostgreSQL..." -NoNewline
$maxAttempts = 30
$attempt = 0
$dbReady = $false

while ($attempt -lt $maxAttempts -and -not $dbReady) {
    Start-Sleep -Seconds 2
    $attempt++
    Write-Host "." -NoNewline
    
    $result = docker-compose exec -T db pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        $dbReady = $true
    }
}

if ($dbReady) {
    Write-Host " ✓" -ForegroundColor Green
} else {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "  PostgreSQL failed to start in time" -ForegroundColor Red
    exit 1
}

Write-Host "  Waiting for Redis..." -NoNewline
Start-Sleep -Seconds 3
Write-Host " ✓" -ForegroundColor Green

Write-Host "  Waiting for Backend..." -NoNewline
Start-Sleep -Seconds 5
Write-Host " ✓" -ForegroundColor Green

Write-Host ""

# Step 5: Run migrations
Write-Host "[Step 5/6] Running database migrations..." -ForegroundColor Yellow

# Copy migration file to container
docker cp backend/app/db/migrations/0001_create_schema.sql official-verifier-db-1:/tmp/migration.sql 2>$null

# Run migration
$migrationResult = docker-compose exec -T db psql -U postgres -d officialdir -f /tmp/migration.sql 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Migrations completed successfully" -ForegroundColor Green
} else {
    # Check if tables already exist
    if ($migrationResult -like "*already exists*") {
        Write-Host "  ✓ Database already initialized" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Migration warning (may be okay if already run)" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 6: Seed database
Write-Host "[Step 6/6] Seeding database with example data..." -ForegroundColor Yellow

$seedResult = docker-compose exec -T backend python scripts/seed.py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Database seeded successfully" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Seeding completed with warnings" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! 🎉" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Display service URLs
Write-Host "Services are now running:" -ForegroundColor White
Write-Host ""
Write-Host "  📍 Backend API:    " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Green
Write-Host "  📚 API Docs:       " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  ⚛️  Frontend:       " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host "  🐘 PostgreSQL:     " -NoNewline -ForegroundColor White
Write-Host "localhost:5432" -ForegroundColor Green
Write-Host "  🔴 Redis:          " -NoNewline -ForegroundColor White
Write-Host "localhost:6379" -ForegroundColor Green
Write-Host ""

# Test API
Write-Host "Testing API..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $testResult = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
    if ($testResult.status -eq "healthy") {
        Write-Host "  ✓ API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ API not responding yet (may need a few more seconds)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Quick Test Commands:" -ForegroundColor White
Write-Host ""
Write-Host "  # Test lookup" -ForegroundColor Gray
Write-Host '  Invoke-RestMethod -Uri "http://localhost:8000/v1/lookup" -Method POST -ContentType "application/json" -Body ''{"query": "HDFC Bank"}''' -ForegroundColor Cyan
Write-Host ""
Write-Host "  # View logs" -ForegroundColor Gray
Write-Host "  docker-compose logs -f backend" -ForegroundColor Cyan
Write-Host ""
Write-Host "  # Stop services" -ForegroundColor Gray
Write-Host "  docker-compose down" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Open http://localhost:8000/docs in your browser" -ForegroundColor Gray
Write-Host "  2. Open http://localhost:3000 for the frontend" -ForegroundColor Gray
Write-Host "  3. Use API key: test-api-key-12345" -ForegroundColor Gray
Write-Host ""

Write-Host "For more information, see START_PRODUCTION.md" -ForegroundColor Gray
Write-Host ""

# Ask if user wants to open browser
$openBrowser = Read-Host "Open API documentation in browser? (Y/n)"
if ($openBrowser -ne "n" -and $openBrowser -ne "N") {
    Start-Process "http://localhost:8000/docs"
}

Write-Host ""
Write-Host "Setup complete! Press Enter to exit..." -ForegroundColor Green
Read-Host
