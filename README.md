# Unified Multimedia Platform

A monorepo combining a Cyber Threat Intelligence (CTI) platform with an AI-powered marketing content engine. Built for security teams to collect, score, and act on threat intelligence — and for marketing teams to turn that intelligence into campaigns.

## Architecture

```
                        Nginx :80
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   /api/v1/intel/   /api/v1/content/   /security/ & /marketing/
          │                │                │
  Intelligence       Content           React SPAs
  Service :8000      Service :3000     (static bundles)
  (Python/FastAPI)   (Node.js/Express)
          │                │
          └────────┬───────┘
                   │
          PostgreSQL + Redis + Ollama
```

**Services**

| Container | Port | Description |
|---|---|---|
| `ump-nginx` | 80 | Reverse proxy + static file server |
| `ump-intelligence-service` | 8000 | CTI collection, SAINT scoring, unified intel API |
| `ump-content-service` | 3000 | AI content generation, approval queue, LinkedIn posting |
| `ump-celery-worker` | — | Background collection jobs (every 20 min) |
| `ump-celery-beat` | — | Job scheduler |
| `ump-postgres` | 5432 | Primary database |
| `ump-redis` | 6379 | Celery broker + cache |
| `ump-ollama` | 11434 | Local LLM for intel enrichment |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- At least one LLM API key (Anthropic recommended) — or Ollama runs locally with no key required

---

## Quick Start (Docker Compose)

> **Note:** The unified platform services (`intelligence-service`, `content-service`, and both dashboards) are currently under active development. For a fully functional experience right now, use the [legacy standalone products](#legacy-standalone-products) below.

### 1. Clone and configure

```bash
git clone <repo-url>
cd multi-media-tool

cp .env.example .env
```

Edit `.env` and fill in the required values:

```env
# Required
POSTGRES_PASSWORD=your-secure-password
JWT_SECRET=your-long-random-secret-min-32-chars

# At least one LLM provider key
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# OPENROUTER_API_KEY=sk-or-...
# GEMINI_API_KEY=AIza...
```

All other values have working defaults. LinkedIn, Slack, and Teams keys are optional.

### 2. Pull the Ollama model (first run only)

```bash
docker compose up ollama -d
docker exec ump-ollama ollama pull llama3.2
```

### 3. Start all services

```bash
docker compose up
```

Or run in the background:

```bash
docker compose up -d
docker compose logs -f   # tail logs
```

### 4. Open the dashboards

| URL | Description |
|---|---|
| http://localhost/ | Redirects to Security Dashboard |
| http://localhost/security/ | Security analyst dashboard |
| http://localhost/marketing/ | Marketing team dashboard |
| http://localhost:8000/docs | Intelligence Service API docs (Swagger) |
| http://localhost:3000/docs | Content Service API docs |

### Useful commands

```bash
# Stop all services
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v

# Rebuild a single service after code changes
docker compose up --build intelligence-service

# View logs for a specific service
docker compose logs -f intelligence-service

# Check service health
docker compose ps
```

---

## Legacy Standalone Products

Both original products are fully functional and can be run independently without Docker.

### Zero Day Radar (CTI Platform)

FastAPI backend on `:8009` + React frontend on `:5173`.

**Backend**

```bash
cd zero_day_radar/backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # add optional API keys

# Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8009
```

API docs: http://localhost:8009/docs

**Background jobs** (optional — runs collection every 20 min)

Open separate terminals for each:

```bash
# Terminal 1 — Redis (if not already running)
./scripts/start_redis_local.sh

# Terminal 2 — Celery worker
./scripts/start_celery_worker.sh

# Terminal 3 — Celery beat scheduler
./scripts/start_celery_beat.sh

# Or run all three at once
./scripts/start_background.sh
```

**Manual pipeline triggers**

```bash
python -m scripts.run_unified_pipeline    # full collection + LLM enrichment
python -m scripts.refresh_intel          # social + advisories + blogs
python -m scripts.refresh_vulnerabilities # CVE / NVD / CISA KEV
```

**Frontend**

```bash
cd zero_day_radar/frontend
pnpm install
pnpm dev     # http://localhost:5173
```

**Optional API keys** (set in `zero_day_radar/backend/.env` with `ZDR_` prefix):

| Key | Purpose |
|---|---|
| `ZDR_REDDIT_CLIENT_ID` / `ZDR_REDDIT_CLIENT_SECRET` | Reddit search |
| `ZDR_GITHUB_TOKEN` | Higher GitHub API rate limits |
| `ZDR_NVD_API_KEY` | Higher NVD rate limits |
| `ZDR_NITTER_INSTANCES` | Comma-separated Nitter URLs for X/Twitter |

Sources without keys still work (RSS, HackerNews, CISA KEV, NVD).

---

### OpenOSINT (OSINT + Marketing Platform)

OSINT API on `:8000`, Marketing API on `:3002`, OSINT dashboard on `:5173`, Marketing dashboard on `:5174`.

**OSINT Core**

```bash
cd OpenOSINT

pip install -e ".[all]"
cp .env .env.local    # add your API keys

# Start the API (auto-seeds DB + starts background watcher on first run)
uvicorn openosint.api.main:app --reload --port 8000
```

Verify: http://localhost:8000/health

**CLI (no server needed)**

```bash
openosint                              # interactive REPL
openosint intel --query "ransomware"   # live CVE/CISA feed
openosint company example.com          # full company OSINT scan
openosint email target@example.com     # email footprint
openosint --help                       # all commands
```

**OSINT Dashboard**

```bash
cd OpenOSINT/frontend
npm install
npm run dev    # http://localhost:5173
```

**Marketing Module**

```bash
cd OpenOSINT/marketing
npm install

# Terminal 1 — Marketing API
npm run dev:api    # http://localhost:3002

# Terminal 2 — Marketing Dashboard
npm run dev:ui     # http://localhost:5174
```

**Optional API keys** (set in `OpenOSINT/.env`):

| Key | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | AI content generation (recommended) |
| `OPENAI_API_KEY` | Alternative AI provider |
| `OPENROUTER_API_KEY` | 200+ models via one key |
| `GEMINI_API_KEY` | Google Gemini |
| `HIBP_API_KEY` | HaveIBeenPwned breach checks |
| `SHODAN_API_KEY` | Shodan host intelligence |
| `VIRUSTOTAL_API_KEY` | VirusTotal reputation |
| `GITHUB_TOKEN` | GitHub API (60 → 5000 req/h) |
| `IPINFO_TOKEN` | IP geolocation |
| `ABUSEIPDB_API_KEY` | AbuseIPDB reputation |

Only one LLM key is required. All OSINT keys are optional — tools degrade gracefully.

---

## Environment Variables Reference

Full reference in `.env.example`. Key groups:

| Group | Variables |
|---|---|
| Database | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL` |
| Redis | `REDIS_URL` |
| Auth | `JWT_SECRET` |
| LLM providers | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY` |
| LinkedIn OAuth | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` |
| Notifications | `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL` |
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_PORT` |

---

## Development

### Running tests

```bash
# Intelligence Service (Python)
cd intelligence-service
pytest
pytest --hypothesis-seed=0    # deterministic property tests

# Content Service (Node.js)
cd content-service
npm test

# OpenOSINT
cd OpenOSINT
pytest tests/

# OpenOSINT Marketing
cd OpenOSINT/marketing
npm test
```

### Building dashboards for production

```bash
# Security Dashboard
cd security-dashboard
npm install && npm run build    # output → dist/

# Marketing Dashboard
cd marketing-dashboard
npm install && npm run build    # output → dist/
```

Nginx mounts both `dist/` folders as static files automatically when running via Docker Compose.

### Database migrations

```bash
# Intelligence Service (Alembic)
cd intelligence-service
alembic upgrade head
alembic revision --autogenerate -m "description"

# Content Service (Prisma)
cd content-service
npx prisma migrate dev          # apply + generate client
npx prisma generate             # regenerate client only
npx prisma studio               # visual DB browser
```
