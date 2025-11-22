# Starting the Full Production Version

## Prerequisites

### 1. Start Docker Desktop

**Docker Desktop is required but not currently running.**

**To start Docker Desktop:**

1. **Find Docker Desktop** in your Start Menu
2. **Click to launch** Docker Desktop
3. **Wait** for the Docker icon in system tray to show "Docker Desktop is running"
4. **Verify** by running: `docker ps`

**Alternative**: If Docker Desktop is not installed:
- Download from: https://www.docker.com/products/docker-desktop/
- Install and restart your computer
- Launch Docker Desktop

---

## Once Docker is Running

### Step 1: Start All Services

```powershell
cd official-verifier
docker-compose up --build
```

This will start:
- 🐘 **PostgreSQL 15** (port 5432)
- 🔴 **Redis 7** (port 6379)
- 🐍 **Backend API** (port 8000)
- ⚛️ **Frontend** (port 3000)

**Wait for**: "Application startup complete" message

---

### Step 2: Run Database Migrations

In a **new terminal**:

```powershell
cd official-verifier
docker-compose exec db psql -U postgres -d officialdir -f /docker-entrypoint-initdb.d/0001_create_schema.sql
```

Or use the migration script:

```powershell
# Make script executable (Git Bash or WSL)
chmod +x scripts/migrate.sh
./scripts/migrate.sh

# Or run SQL directly
docker-compose exec db psql -U postgres -d officialdir < backend/app/db/migrations/0001_create_schema.sql
```

---

### Step 3: Seed the Database

```powershell
docker-compose exec backend python scripts/seed.py
```

This creates:
- ✅ HDFC Bank entity (score: 100)
- ✅ PayPal entity (score: 67.5)
- ✅ Test API key: `test-api-key-12345`
- ✅ Example lookalike domains

---

### Step 4: Verify Everything Works

**Test the API:**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/lookup" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query": "HDFC Bank"}' | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
  "ok": true,
  "data": {
    "entity_id": "uuid",
    "name": "HDFC Bank",
    "official_domain": "hdfcbank.com",
    "confidence_score": 100.0,
    "risk_level": "none"
  }
}
```

---

### Step 5: Access the Services

| Service | URL | Description |
|---------|-----|-------------|
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Frontend** | http://localhost:3000 | React App |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Cache |

---

## Using Makefile (Easier)

If you have `make` installed:

```bash
make dev      # Start all services
make migrate  # Run migrations
make seed     # Seed database
make test     # Run tests
make logs     # View logs
make down     # Stop services
```

---

## Troubleshooting

### Docker Desktop Not Starting?

1. **Check if Hyper-V is enabled** (Windows Pro/Enterprise)
2. **Check if WSL 2 is installed** (Windows Home)
3. **Restart your computer**
4. **Check Docker Desktop logs** in the app

### Port Already in Use?

Edit `docker-compose.yml` to change ports:

```yaml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Database Connection Error?

Wait for PostgreSQL to be ready:

```powershell
docker-compose logs db
# Look for: "database system is ready to accept connections"
```

### Migration Failed?

Check if database exists:

```powershell
docker-compose exec db psql -U postgres -l
```

Create database manually if needed:

```powershell
docker-compose exec db psql -U postgres -c "CREATE DATABASE officialdir;"
```

---

## Stopping the Services

```powershell
# Stop services (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## Next Steps After Setup

### 1. Run the Harvester

```powershell
docker-compose exec backend python -m app.harvest run_once
```

This will:
- Fetch data from Wikipedia
- Fetch data from iTunes
- Fetch data from Play Store
- Update entity scores

### 2. Create Additional API Keys

```powershell
docker-compose exec backend python scripts/create_api_key.py "my-secret-key" "Production Key" 100
```

### 3. View Database

```powershell
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d officialdir

# Run queries
SELECT * FROM entities;
SELECT * FROM verifications;
\q  # Exit
```

### 4. Monitor Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
```

---

## Production Deployment

For production deployment, update:

1. **Environment Variables** (`.env`):
   ```
   ENV=production
   SECRET_KEY=<strong-random-key>
   DATABASE_DSN=<production-db-url>
   REDIS_URL=<production-redis-url>
   ```

2. **Use Managed Services**:
   - PostgreSQL: AWS RDS, Google Cloud SQL
   - Redis: AWS ElastiCache, Redis Cloud

3. **Enable HTTPS**:
   - Use nginx or Traefik as reverse proxy
   - Get SSL certificate (Let's Encrypt)

4. **Set up Monitoring**:
   - Add Sentry DSN
   - Enable Prometheus metrics
   - Set up log aggregation

---

## Quick Reference

```powershell
# Start everything
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec db psql -U postgres -d officialdir -f /docker-entrypoint-initdb.d/0001_create_schema.sql

# Seed data
docker-compose exec backend python scripts/seed.py

# Run harvester
docker-compose exec backend python -m app.harvest run_once

# Stop everything
docker-compose down
```

---

## Support

If you encounter issues:

1. Check Docker Desktop is running
2. Check logs: `docker-compose logs`
3. Verify ports are available
4. Try restarting Docker Desktop
5. Check the TROUBLESHOOTING.md file

---

**Ready to start?** 

1. ✅ Start Docker Desktop
2. ✅ Run `docker-compose up --build`
3. ✅ Run migrations
4. ✅ Seed database
5. ✅ Test the API

Let me know when Docker Desktop is running and I'll help you through the setup! 🚀
