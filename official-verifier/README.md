# Official Website Verification Platform

A production-ready platform for verifying official websites and preventing scams through cross-verification and confidence scoring.

## Features

- ✅ **Entity Verification**: Verify official websites using multiple data sources
- 🔍 **Smart Search**: Fuzzy search by company name or domain
- 📊 **Confidence Scoring**: Deterministic scoring engine with explainable results
- 🚨 **Scam Detection**: Identify lookalike domains and typosquatting attempts
- 🔄 **Data Harvesting**: Automated collection from Wikipedia, App Store, Play Store
- 🔐 **API Key Authentication**: Secure API access with rate limiting
- 📈 **Admin Dashboard**: Manage entities, verifications, and submissions

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  (React/TS) │      │   Backend    │      │  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├─────▶ Redis (Cache/Rate Limit)
                            │
                            └─────▶ External APIs
                                    (Wikipedia, iTunes, etc.)
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Run with Docker Compose

```bash
# Clone the repository
cd official-verifier

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build

# In another terminal, run migrations
docker-compose exec backend python -c "
import asyncio
from app.db.base import db
asyncio.run(db.connect())
"

# Or use the migration script
chmod +x scripts/migrate.sh
./scripts/migrate.sh

# Seed the database with example data
docker-compose exec backend python scripts/seed.py
```

The services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Test API Key

After seeding, use this API key for testing:
```
X-API-Key: test-api-key-12345
```

## Database Setup

### Run Migrations

```bash
# Using Docker
docker-compose exec db psql -U postgres -d officialdir -f /app/backend/app/db/migrations/0001_create_schema.sql

# Or locally
psql postgresql://postgres:postgres@localhost:5432/officialdir -f backend/app/db/migrations/0001_create_schema.sql
```

### Seed Data

```bash
docker-compose exec backend python scripts/seed.py
```

This creates:
- HDFC Bank entity with Wikipedia + App Store verifications (score: 100)
- PayPal entity with Wikipedia verification
- Test API key: `test-api-key-12345`
- Example lookalike domain

## API Usage

### Lookup Entity

```bash
curl -X POST http://localhost:8000/v1/lookup \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{"query": "HDFC Bank"}'
```

Response:
```json
{
  "ok": true,
  "data": {
    "entity_id": "uuid",
    "name": "HDFC Bank",
    "official_domain": "hdfcbank.com",
    "confidence_score": 100.0,
    "risk_level": "none",
    "verification_sources": [
      {"source_type": "wikipedia", "url": "...", "score": 67.5},
      {"source_type": "appstore", "url": "...", "score": 75.0}
    ],
    "similar_domains": [
      {"domain": "hdfcbank-secure.co", "risk": "high", "similarity": 0.92}
    ]
  }
}
```

### Get Entity Details

```bash
curl -X GET http://localhost:8000/v1/entities/{entity_id} \
  -H "X-API-Key: test-api-key-12345"
```

### Submit Domain

```bash
curl -X POST http://localhost:8000/v1/submissions \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "submitted_by": "user@example.com",
    "entity_name": "Example Corp",
    "domain": "example.com",
    "evidence": {"note": "Official website"}
  }'
```

### Admin Endpoints

```bash
# Create entity
curl -X POST http://localhost:8000/v1/admin/entities \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Company",
    "entity_type": "company",
    "country_iso2": "US"
  }'

# Recompute score
curl -X POST http://localhost:8000/v1/admin/recompute/{entity_id} \
  -H "X-API-Key: test-api-key-12345"
```

## Harvester

Run the harvester to collect data from external sources:

```bash
# Run once
docker-compose exec backend python -m app.harvest run_once

# Or locally
cd backend
python -m app.harvest run_once
```

The harvester:
1. Searches Wikipedia (Wikidata P856)
2. Searches Apple App Store
3. Searches Google Play Store (best-effort)
4. Creates verifications with appropriate scores
5. Recomputes entity confidence

## Scoring System

### Signal Presets

| Source | Base Score | Weight | Total Contribution |
|--------|-----------|--------|-------------------|
| Wikipedia | 45.0 | 1.5 | 67.5 |
| App Store | 50.0 | 1.5 | 75.0 |
| Play Store | 50.0 | 1.5 | 75.0 |
| Gov Registry | 60.0 | 2.0 | 120.0 |
| WHOIS Age (>1yr) | 15.0 | 1.0 | 15.0 |
| SSL CN Match | 15.0 | 1.1 | 16.5 |
| Lookalike Penalty | -40.0 | 1.0 | -40.0 |

### Risk Levels

- **None** (90-100): Highly verified, safe
- **Low** (60-89): Verified with some signals
- **Medium** (30-59): Limited verification
- **High** (0-29): Unverified or suspicious

### Score Calculation

```python
score = sum(score_contrib * weight for each verification)
- Apply 0.5x multiplier for expired verifications
- Subtract 40 points for flagged lookalikes
- Cap final score between 0 and 100
```

## Testing

### Run Unit Tests

```bash
cd backend
pytest app/tests/test_scoring.py -v
```

### Run Integration Tests

```bash
pytest app/tests/test_api.py -v
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Generate API Key Hash

```bash
# Dev endpoint (only available in ENV=dev)
curl -X POST http://localhost:8000/dev/hash-key?key=my-secret-key
```

## CI/CD

GitHub Actions workflow included at `.github/workflows/ci.yml`:

- Linting (flake8, ESLint)
- Unit tests
- Integration tests
- Docker image builds

## Production Deployment

### Environment Variables

```bash
ENV=production
DATABASE_DSN=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=<strong-random-key>
SENTRY_DSN=<optional-sentry-dsn>
RATE_LIMIT_FREE_PER_MIN=30
```

### Security Checklist

- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Use connection pooling
- [ ] Enable rate limiting
- [ ] Set up monitoring (Sentry)
- [ ] Regular database backups
- [ ] Rotate API keys periodically

### Scaling

- Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Use managed Redis (AWS ElastiCache, Redis Cloud)
- Deploy backend with Kubernetes or ECS
- Use CDN for frontend (CloudFront, Cloudflare)
- Enable database read replicas
- Implement caching strategy

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics

```bash
curl http://localhost:8000/metrics
```

Returns:
- `lookup_requests_total`
- `avg_latency_ms`
- `harvester_success`
- `harvester_failures`

## API Documentation

Full OpenAPI documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linters and tests
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: See `/docs` folder
- API Docs: http://localhost:8000/docs
