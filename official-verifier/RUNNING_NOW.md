# 🎉 Official Website Verifier - NOW RUNNING!

## ✅ What's Running

### 1. **Backend API** - http://localhost:8000
- Status: ✅ **RUNNING**
- Mode: Demo (in-memory mock data)
- Process ID: 3

### 2. **API Documentation** - http://localhost:8000/docs
- Interactive Swagger UI
- Test all endpoints directly in browser

### 3. **Demo Frontend** - demo.html
- Beautiful web interface
- Search for companies
- View verification results

## 🧪 Test the API

### Example 1: Search for HDFC Bank
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/lookup" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query": "HDFC Bank"}' | ConvertTo-Json -Depth 10
```

**Result:**
```json
{
  "ok": true,
  "data": {
    "entity_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "HDFC Bank",
    "official_domain": "hdfcbank.com",
    "confidence_score": 100.0,
    "risk_level": "none",
    "verification_sources": [
      {"source_type": "wikipedia", "score": 67.5},
      {"source_type": "appstore", "score": 75.0}
    ],
    "similar_domains": [
      {"domain": "hdfcbank-secure.co", "risk": "high"}
    ]
  }
}
```

### Example 2: Check a Domain
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/domains/check" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"domain": "paypal.com"}' | ConvertTo-Json
```

**Result:**
```json
{
  "ok": true,
  "domain": "paypal.com",
  "known": true,
  "entity_name": "PayPal",
  "confidence_score": 67.5,
  "risk_level": "low"
}
```

### Example 3: Unknown Domain
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/v1/domains/check" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"domain": "suspicious-bank.com"}' | ConvertTo-Json
```

**Result:**
```json
{
  "ok": true,
  "domain": "suspicious-bank.com",
  "known": false,
  "risk_level": "unknown",
  "message": "Domain not in verified database"
}
```

## 📊 Available Endpoints

### Public Endpoints
- `POST /v1/lookup` - Search by company name or domain
- `GET /v1/entities/{id}` - Get entity details
- `POST /v1/submissions` - Submit a domain for verification
- `POST /v1/domains/check` - Quick domain risk check

### System Endpoints
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🎯 Demo Data Available

1. **HDFC Bank**
   - Domain: hdfcbank.com
   - Score: 100.0
   - Risk: None
   - Sources: Wikipedia, App Store

2. **PayPal**
   - Domain: paypal.com
   - Score: 67.5
   - Risk: Low
   - Sources: Wikipedia

3. **Google**
   - Domain: google.com
   - Score: 100.0
   - Risk: None
   - Sources: Wikipedia, App Store

## 🌐 Access Points

| Service | URL | Status |
|---------|-----|--------|
| API | http://localhost:8000 | ✅ Running |
| API Docs | http://localhost:8000/docs | ✅ Available |
| Demo UI | demo.html | ✅ Open in browser |

## 🛑 To Stop the Server

```powershell
# Press Ctrl+C in the terminal where the server is running
# Or use the process ID:
Stop-Process -Id 8864
```

## 📝 What This Demonstrates

✅ **API Key Authentication** (simplified for demo)
✅ **Confidence Scoring** (100 = highly verified, 0 = unverified)
✅ **Risk Level Calculation** (none, low, medium, high)
✅ **Verification Sources** (Wikipedia, App Store, etc.)
✅ **Lookalike Domain Detection** (scam prevention)
✅ **RESTful API Design**
✅ **Interactive Documentation**
✅ **Modern Web UI**

## 🚀 Next Steps

### For Full Production Version:
1. **Start Docker Desktop** and run:
   ```bash
   docker-compose up --build
   ```

2. **Run Migrations:**
   ```bash
   docker-compose exec backend python scripts/seed.py
   ```

3. **Access Full Features:**
   - PostgreSQL database
   - Redis caching
   - Rate limiting
   - Data harvesters
   - Admin endpoints
   - React frontend

## 💡 Tips

- Use the **Swagger UI** at http://localhost:8000/docs to test all endpoints interactively
- Open **demo.html** in your browser for a visual interface
- Try searching for different companies and domains
- Check the server logs to see API requests in real-time

## 🎓 Key Features Demonstrated

1. **Entity Verification**: Verify if a website is official
2. **Confidence Scoring**: 0-100 score based on multiple sources
3. **Risk Assessment**: Automatic risk level calculation
4. **Scam Detection**: Identify lookalike/typosquatting domains
5. **Multi-Source Verification**: Wikipedia, App Store, etc.
6. **RESTful API**: Clean, well-documented endpoints
7. **Modern UI**: Beautiful, responsive interface

---

**Status**: ✅ **RUNNING AND READY TO USE!**

**Demo Mode**: Using in-memory mock data (no database required)

**Full Version**: Available via Docker Compose (requires Docker Desktop)
