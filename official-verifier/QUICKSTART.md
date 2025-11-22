# Quick Start Guide

Get the Official Website Verification Platform running in 5 minutes.

## Step 1: Start Services

```bash
cd official-verifier
docker-compose up --build
```

Wait for all services to start (PostgreSQL, Redis, Backend, Frontend).

## Step 2: Run Migrations

In a new terminal:

```bash
# Connect to database and run migrations
docker-compose exec db psql -U postgres -d officialdir -f /tmp/0001_create_schema.sql
```

Or use the migration script:

```bash
chmod +x scripts/migrate.sh
./scripts/migrate.sh
```

## Step 3: Seed Database

```bash
docker-compose exec backend python scripts/seed.py
```

This creates:
- HDFC Bank (confidence: 100)
- PayPal (confidence: 67.5)
- Test API key: `test-api-key-12345`

## Step 4: Test the API

```bash
curl -X POST http://localhost:8000/v1/lookup \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"query": "HDFC Bank"}'
```

Expected response:
```json
{
  "ok": true,
  "data": {
    "entity_id": "...",
    "name": "HDFC Bank",
    "official_domain": "hdfcbank.com",
    "confidence_score": 100.0,
    "risk_level": "none",
    "verification_sources": [...]
  }
}
```

## Step 5: Open Frontend

Visit http://localhost:3000 and search for "HDFC Bank" or "PayPal".

## Using Make Commands

```bash
make dev      # Start all services
make migrate  # Run migrations
make seed     # Seed database
make test     # Run tests
make logs     # View logs
make down     # Stop services
```

## Next Steps

- Read the full [README.md](README.md)
- Explore API docs at http://localhost:8000/docs
- Run the harvester: `make harvest`
- Create custom API keys: `python scripts/create_api_key.py`

## Troubleshooting

**Database connection error?**
```bash
docker-compose down -v
docker-compose up --build
```

**Port already in use?**
Edit `docker-compose.yml` to change ports.

**Frontend not loading?**
```bash
docker-compose logs frontend
```

Check that backend is running on port 8000.
