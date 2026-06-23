# SQ1 OSINT API — Integration Guide for Marketing Module

Base URL: `http://localhost:8000`

## Endpoints Person 2 should use

```
GET  /api/intel/latest
     Returns: [{id, title, classification, severity, summary, cveIds, tags,
                timestamp, sourceVerified, isMisinformation}]

GET  /api/intel/by-type/{type}
     type: VULNERABILITY | THREAT | COMPLIANCE | BREACH | MISINFORMATION

GET  /api/intel/unmarketed
     Items not yet used in any marketing campaign

POST /api/intel/{id}/mark-used
     Call this after creating a marketing asset for this intel item

GET  /api/companies
     Returns: [{id, name, domain, threatScore, lastScan, employeeCount}]

GET  /health
     Returns: {"status": "ok"} — use to check if API is running
```

## CORS

Allowed origins: `http://localhost:5173`, `http://localhost:5174` (Person 2's Vite port)

## Intel item schema

```json
{
  "id": "string",
  "title": "string",
  "classification": "VULNERABILITY|THREAT|COMPLIANCE|BREACH|MISINFORMATION",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "summary": "string",
  "cveIds": ["CVE-XXXX-XXXXX"],
  "tags": ["string"],
  "timestamp": "ISO8601",
  "sourceVerified": true,
  "isMisinformation": false,
  "usedInMarketing": false
}
```

## Quick start (curl examples)

```bash
# Get latest intel
curl http://localhost:8000/api/intel/latest

# Get only vulnerability items
curl http://localhost:8000/api/intel/by-type/VULNERABILITY

# Get items not yet marketed
curl http://localhost:8000/api/intel/unmarketed

# Mark an item as used in marketing
curl -X POST http://localhost:8000/api/intel/abc123/mark-used

# Health check
curl http://localhost:8000/health
```

## Running the backend

```bash
# Install deps
pip install fastapi uvicorn tinydb httpx anthropic apscheduler python-dotenv

# Start the API (from repo root)
uvicorn openosint.api.main:app --reload --port 8000

# Seed demo data (first run)
python -m openosint.data.seed
```

## Notes

- All endpoints return JSON
- `sourceVerified` is `true` when the source domain is in the trusted whitelist
- `isMisinformation` is `true` when Claude flags it — suppress from feeds
- The watcher auto-refreshes intel every 60 seconds when running
