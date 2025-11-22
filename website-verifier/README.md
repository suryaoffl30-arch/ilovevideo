# Website Verifier

A web application that provides only official website links to mitigate scams through cross-verification. It includes an API for safe redirects.

## Features

- ✅ Verify if a URL is an official website
- 🔍 Search for official websites by company name
- ⚠️ Detect potential scam sites (typosquatting)
- 🔄 API for safe redirects
- 📊 Cross-verification system

## Project Structure

```
website-verifier/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   └── verifier.py      # Verification logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── App.css          # Styles
│   │   └── main.tsx         # Entry point
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── verified_sites.json      # Database of verified sites
```

## Setup

### Backend

```bash
cd website-verifier/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs on: http://localhost:8000

### Frontend

```bash
cd website-verifier/frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## API Endpoints

### POST /api/verify
Verify if a URL is official and safe.

**Request:**
```json
{
  "url": "https://paypal.com"
}
```

**Response:**
```json
{
  "verified": true,
  "official_url": "https://www.paypal.com",
  "name": "PayPal",
  "confidence": 100,
  "warning": null
}
```

### POST /api/search
Search for official websites by name.

**Request:**
```json
{
  "name": "PayPal"
}
```

**Response:**
```json
{
  "results": [
    {
      "name": "PayPal",
      "official_url": "https://www.paypal.com",
      "domain": "paypal.com",
      "category": "payment"
    }
  ],
  "count": 1
}
```

### GET /api/redirect/{domain}
Safe redirect endpoint - returns official URL for a domain.

**Example:** `/api/redirect/paypal.com`

**Response:**
```json
{
  "redirect_to": "https://www.paypal.com",
  "safe": true
}
```

## Adding Verified Sites

Edit `verified_sites.json` to add more verified websites:

```json
{
  "sites": [
    {
      "name": "Company Name",
      "domain": "example.com",
      "official_url": "https://www.example.com",
      "category": "category_name"
    }
  ]
}
```

## How It Works

1. **Exact Match**: Checks if the domain exactly matches a verified site
2. **Similarity Detection**: Uses fuzzy matching to detect typosquatting (e.g., "paypai.com" vs "paypal.com")
3. **Cross-Verification**: Maintains a curated database of official websites
4. **Safe Redirects**: API endpoint ensures users are redirected to verified URLs only

## Security Features

- Domain normalization (removes www, converts to lowercase)
- Typosquatting detection (80% similarity threshold)
- Warning system for suspicious domains
- CORS enabled for API integration

## Use Cases

- Browser extensions for safe browsing
- Email link verification
- Mobile app integrations
- Corporate security tools
- Educational platforms
