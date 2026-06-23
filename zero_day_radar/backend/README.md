# Zero Day Radar — Backend

FastAPI backend for the SAINT Threat Intelligence Hunter pipeline.

## Architecture

Staged SQLite pipeline (primary flow):

```
Stage 1 → X/LinkedIn scrape     → researcher_social_posts
Stage 2 → Researcher blogs RSS  → researcher_blog_posts
Stage 3 → Vendor advisories     → vendor_advisory_posts
Stage 4 → CVE/NVD/KEV/GitHub    → cve_findings
Stage 5 → Score & correlate     → scored_posts (dashboard)
```

SQLite database: `backend/data/zero_day_radar.db`

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional API keys
uvicorn app.main:app --reload --host 0.0.0.0 --port 8009
```

API docs: http://localhost:8009/docs

## Background Jobs (Celery + Redis on localhost)

All collectors run automatically every **20 minutes** and upsert into SQLite:

| Pipeline | Table | Sources |
|----------|-------|---------|
| Social | `intel_posts` | Nitter/Twitter, Reddit, HackerNews, LinkedIn |
| Advisories | `vendor_advisory_intel` | MSRC, Cisco, Fortinet, etc. |
| Blogs | `research_blog_intel` | Project Zero, Unit42, Krebs, etc. |
| Vulnerabilities | `vulnerability_intel` | CVE Program, NVD, CISA KEV, GitHub, Exploit-DB, Metasploit |
| Compliance | `compliance_intel` | NIST, ISO, PCI SSC, ENISA, EDPB, CISA, EU AI Act, vendor compliance |
| **Unified (Ollama)** | **`unified_intel`** | **All tables → vendor/product/version + SAINT score** |

**1. Install Redis on localhost (no Docker):**

```bash
sudo apt update && sudo apt install -y redis-server
sudo service redis-server start
redis-cli ping   # should return PONG
```

**2. Start background worker + beat:**

```bash
cd backend
chmod +x scripts/*.sh
./scripts/start_background.sh
```

Or run in separate terminals:

```bash
./scripts/start_redis_local.sh
./scripts/start_celery_worker.sh
./scripts/start_celery_beat.sh
```

**3. FastAPI (separate terminal):**

```bash
uvicorn app.main:app --reload --port 8009
```

**Manual trigger / status:**

```bash
curl -X POST http://localhost:8009/api/v1/jobs/run/all
curl http://localhost:8009/api/v1/jobs/status/<task_id>
curl http://localhost:8009/api/v1/health/worker
```

Dependencies are in `requirements.txt`: `celery[redis]`, `redis`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Service health |
| **POST** | **`/api/v1/pipeline/run`** | **Run staged pipeline (SQLite)** |
| GET | `/api/v1/pipeline/runs` | List past pipeline runs |
| GET | `/api/v1/pipeline/runs/{hunt_id}` | Get run details + posts |
| GET | `/api/v1/posts` | List scored posts for dashboard |
| GET | `/api/v1/posts/{post_id}` | Single post detail |
| POST | `/api/v1/hunt` | Legacy parallel hunt (no DB) |
| GET | `/api/v1/sources` | List all intelligence sources |
| GET | `/api/v1/keywords` | List configured keywords |
| GET | `/api/v1/compliance/sources` | List compliance intel sources (Tier 1/2) |
| POST | `/api/v1/compliance/search` | Search compliance sources → `compliance_intel` |
| GET | `/api/v1/compliance` | List stored compliance findings |

## Step 5: Compliance Intelligence

SQLite table: `compliance_intel`

Tier 1 (highest priority): NIST, ISO, PCI SSC, ENISA, EDPB, CISA Guidance, EU AI Act, IAPP

```bash
curl http://localhost:8009/api/v1/compliance/sources
curl http://localhost:8009/api/v1/compliance/keywords

curl -X POST http://localhost:8009/api/v1/compliance/search \
  -H "Content-Type: application/json" \
  -d '{
    "frameworks": ["ISO 27001", "PCI DSS", "GDPR"],
    "lookback_days": 90,
    "min_confidence": 0.5
  }'

curl "http://localhost:8009/api/v1/compliance?source_tier=1&min_score=0.7"
```

## Unified Intelligence (Ollama + One Table)

SQLite table: `unified_intel`

Pipeline: run all 5 collectors → read all intel tables → Ollama extracts vendor/product/version → SAINT score → one row per cluster.

`classification` column is **NULL** by default (you set taxonomy later).

Requires [Ollama](https://ollama.com) running locally: `ollama pull llama3.2`

```bash
# Check Ollama status
curl http://localhost:8009/api/v1/unified/status

# Full pipeline (collections + LLM + unified table)
curl -X POST http://localhost:8009/api/v1/unified/run \
  -H "Content-Type: application/json" \
  -d '{
    "lookback_days": 30,
    "run_collections": true,
    "use_llm": true,
    "replace_existing": false,
    "min_confidence": 30
  }'

# List unified findings
curl "http://localhost:8009/api/v1/unified?min_score=40&limit=20"

# Script
python -m scripts.run_unified_pipeline
```

## Step 3: Researcher Blogs

SQLite table: `research_blog_intel`

```bash
curl http://localhost:8000/api/v1/blogs/sources

curl -X POST http://localhost:8000/api/v1/blogs/search \
  -H "Content-Type: application/json" \
  -d '{"vendors": ["Fortinet", "Cisco"], "lookback_days": 90}'

curl "http://localhost:8000/api/v1/blogs?source_id=unit42&min_score=0.5"
```

## Step 2: Vendor Advisories

SQLite table: `vendor_advisory_intel`

```bash
# List all advisory sources (MSRC, Cisco, Fortinet, etc.)
curl http://localhost:8000/api/v1/advisories/sources

# Search advisories using vendor + vulnerability keywords
curl -X POST http://localhost:8000/api/v1/advisories/search \
  -H "Content-Type: application/json" \
  -d '{
    "vendors": ["Fortinet", "Microsoft", "Cisco"],
    "lookback_days": 90,
    "min_confidence": 0.4
  }'

# Get stored advisories
curl "http://localhost:8000/api/v1/advisories?vendor=Fortinet&min_score=0.7"
```

## Step 1: Social Search (X, Reddit, LinkedIn, HackerNews)

Single SQLite table: `intel_posts`

```bash
# Preview search queries: [VENDOR] + [VULNERABILITY KEYWORD]
curl "http://localhost:8000/api/v1/social/queries?vendors=Fortinet,Cisco"

# Run search — X/Twitter via Nitter (no API key needed)
curl -X POST http://localhost:8000/api/v1/social/search \
  -H "Content-Type: application/json" \
  -d '{
    "vendors": ["Fortinet", "Cisco", "VMware"],
    "sources": ["twitter", "reddit", "hackernews", "linkedin"],
    "lookback_days": 7,
    "min_confidence": 0.3
  }'

# Get stored posts (latest first, with scores)
curl "http://localhost:8000/api/v1/social/posts?min_score=0.5&limit=20"
```

## Pipeline Request Example

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "products": ["Fortinet", "Cisco ISE"],
    "lookback_days": 30,
    "min_confidence": 0.5
  }'
```

## Get Scored Posts (Dashboard)

```bash
curl "http://localhost:8000/api/v1/posts?min_confidence=0.7&limit=20"
```

## Sources (50+ configured)

- **Researcher Social**: X/Twitter (API), LinkedIn (scraper), Reddit (API), HackerNews (API)
- **Researcher Blogs**: Project Zero, Krebs, Unit42, DFIR Report, SANS ISC, etc. (RSS)
- **Vendor Advisories**: MSRC, Cisco, Fortinet, Palo Alto, VMware, Ivanti, etc.
- **Vulnerability**: CVE Program, NVD, CISA KEV, GitHub PoC, Exploit-DB, Metasploit

## Scoring Model (SAINT Threat Engine)

Score = sum(source scores) + bonuses, capped at **100**.

| Source | Points |
|--------|--------|
| CISA KEV | 40 |
| Vendor Advisory | 30 |
| Project Zero / watchTowr / Unit42 | 20 |
| GitHub PoC / ExploitDB / Metasploit / PacketStorm | 20-25 |
| Krebs / DFIR / blogs | 15 |
| CVE Program | 15 |
| X / LinkedIn | 5 |
| Reddit / HackerNews | 3 |
| NVD | 5 |

**Bonuses:** 2 signals +10 | 3+ signals +15 | PoC +15 | Active exploitation +20 | CVE +10

**Risk levels:** 0-20 LOW | 21-40 MEDIUM | 41-60 HIGH | 61-80 VERY_HIGH | 81-100 CRITICAL

```bash
curl -X POST http://localhost:8009/api/v1/threat/score \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_name": "Fortinet",
    "product_name": "FortiOS",
    "sources": [
      {"source_type": "Vendor Advisory", "source_name": "Vendor Advisory"},
      {"source_id": "github_poc", "source_name": "GitHub PoC"}
    ],
    "poc_available": true,
    "signal_count": 1
  }'
```

## Compliance Scoring Model (SAINT Engine)

Score = sum(source scores) + bonuses, capped at **100**.

| Factor | Points | Notes |
|--------|--------|-------|
| Tier 1 sources | 18-25 | NIST, ISO, PCI SSC, ENISA, EDPB, CISA, EU AI Act, IAPP |
| Regulatory | 20 | EC, UK NCSC, HHS OCR, SEC |
| Standards bodies | 15-18 | CIS, CSA, OWASP, ISACA |
| Vendor compliance | 12-18 | Microsoft, AWS, GCP, Oracle, SAP, Salesforce |
| 2 independent sources | +10 | Multi-source correlation bonus |
| 3+ independent sources | +15 | Multi-source correlation bonus |
| Framework update | +10 | Detected framework revision |
| New requirement | +12 | Mandatory requirement detected |
| Effective date | +8 | Extracted effective date |
| Compliance deadline | +10 | Extracted deadline |
| Impacted controls | +8 | Control IDs extracted |

**Risk levels:** 0-20 LOW | 21-40 MEDIUM | 41-60 HIGH | 61-80 VERY_HIGH | 81-100 CRITICAL

```bash
curl -X POST http://localhost:8009/api/v1/compliance/score \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "PCI SSC",
    "framework_name": "PCI DSS",
    "sources": [{"source_id": "pci_ssc", "source_name": "PCI SSC"}],
    "framework_update": true,
    "new_requirement": true,
    "signal_count": 1
  }'
```

## Optional API Keys

Set in `.env` for full source coverage (all vars use `ZDR_` prefix):

- `ZDR_NITTER_INSTANCES` — X/Twitter via Nitter (no API key; comma-separated URLs)
- `ZDR_REDDIT_CLIENT_ID` / `ZDR_REDDIT_CLIENT_SECRET` — Reddit search (optional)
- `ZDR_GITHUB_TOKEN` — Higher GitHub API rate limits
- `ZDR_NVD_API_KEY` — Higher NVD rate limits

Sources without credentials still work (RSS, HackerNews, CISA KEV, NVD with rate limits).
