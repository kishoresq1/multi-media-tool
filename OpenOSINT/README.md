# SQ1 OSINT — Cybersecurity Threat Intelligence Platform

A full-stack cybersecurity intelligence platform that continuously pulls live CVEs and known-exploited vulnerabilities, runs OSINT scans on companies and employees, detects misinformation using AI, and feeds cleaned intelligence directly into a marketing automation module.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  OSINT Core (Python)                        port 8000       │
│                                                             │
│  openosint/tools/      ← 23 async OSINT tool functions      │
│  openosint/api/        ← FastAPI REST layer                 │
│  openosint/data/       ← TinyDB persistence + seed data     │
│  openosint/watcher/    ← APScheduler background poller      │
│  openosint/llm.py      ← Multi-provider AI utility          │
│  openosint/mcp_server.py ← MCP protocol server (23 tools)  │
│  openosint/cli.py      ← CLI entry point                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP  /api/*
┌────────────────────▼────────────────────────────────────────┐
│  OSINT Dashboard (React + Vite)             port 5173       │
│                                                             │
│  Live intel feed · Company tracker · Employee leak table    │
│  Post tracker · Dark SOC theme                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Marketing Module (Node.js + Express)       port 3002       │
│                                                             │
│  marketing/src/api/    ← Express REST layer                 │
│  marketing/src/agents/ ← AI content generators             │
│  marketing/data/       ← Lowdb persistence                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP  /api/*
┌────────────────────▼────────────────────────────────────────┐
│  Marketing Dashboard (React + Vite)         port 5174       │
│                                                             │
│  Intel queue · Campaign builder · HyperFrame Studio         │
│  Video composer · Comms panel · Asset gallery               │
└─────────────────────────────────────────────────────────────┘
```

---

## What Each Module Does

### OSINT Core (`openosint/`)

**Continuously monitors the threat landscape:**
- Polls NVD and CISA Known Exploited Vulnerabilities every 60 seconds
- Stores all intel in TinyDB with severity, classification, and CVE IDs
- Flags misinformation via AI before surfacing any item
- Validates source credibility against a curated whitelist

**Multi-provider AI (only one key required):**
- Anthropic Claude, OpenAI, OpenRouter, or Google Gemini
- Auto-detects which provider key is set; override with `--provider`

**Company & employee OSINT:**
- Full company scans — WHOIS, subdomain enumeration, Google dork generation, breach check
- Per-employee dark web exposure via HaveIBeenPwned
- Paste dump search, email footprint enumeration, phone intelligence
- Threat score per company (0–100)

**Post tracking:**
- Finds who else published the same story on Reddit
- Returns engagement metrics (score, comments, author, timestamp)

### Marketing Module (`marketing/`)

**Converts raw intel into campaign-ready content:**
- Pulls unmarketed intel from the OSINT API
- AI-generated email campaigns (Claude with deterministic fallback)
- HyperFrame visual content generator with PNG export
- Video script generation with Remotion player preview
- Slack Block Kit and Microsoft Teams message card alerts
- Subscriber portal and asset gallery

---

## Repository Structure

```
SQ1INT/
├── openosint/
│   ├── tools/                   ← 23 async OSINT tool functions
│   │   ├── search_breach.py     ← HaveIBeenPwned v3
│   │   ├── search_email.py      ← holehe email enumeration
│   │   ├── search_username.py   ← sherlock (300+ platforms)
│   │   ├── search_domain.py     ← sublist3r subdomain enum
│   │   ├── search_whois.py      ← WHOIS registration data
│   │   ├── search_ip.py         ← ipinfo.io geolocation
│   │   ├── search_paste.py      ← psbdmp.ws paste dumps
│   │   ├── search_phone.py      ← phoneinfoga
│   │   ├── generate_dorks.py    ← Google dork generator
│   │   ├── search_dns.py        ← DNS enumeration + misconfig detection
│   │   ├── search_shodan.py     ← Shodan host/banner search
│   │   ├── search_virustotal.py ← VirusTotal 70+ AV engines
│   │   ├── search_censys.py     ← Censys internet scan data
│   │   ├── search_abuseipdb.py  ← AbuseIPDB reputation
│   │   ├── search_github.py     ← GitHub user/commit search
│   │   ├── search_ip2location.py← VPN/Tor/proxy detection
│   │   ├── search_dorks_live.py ← Live SERP via Bright Data
│   │   ├── scrape_url.py        ← Web Unlocker via Bright Data
│   │   ├── search_intel.py      ← NVD CVEs + CISA KEV feed
│   │   ├── validate_source.py   ← Source credibility check
│   │   ├── detect_misinfo.py    ← AI misinfo detection (multi-provider)
│   │   ├── scan_company.py      ← Full company orchestrator
│   │   └── track_post.py        ← Reddit post tracker
│   │
│   ├── api/                     ← FastAPI REST layer (port 8000)
│   │   ├── main.py              ← App entry, CORS, startup
│   │   └── routes/
│   │       ├── intel.py         ← /api/intel/*
│   │       ├── companies.py     ← /api/companies/*
│   │       ├── employees.py     ← /api/employees/*
│   │       └── tracker.py       ← /api/tracker/*
│   │
│   ├── data/
│   │   ├── store.py             ← TinyDB wrapper
│   │   └── seed.py              ← 5 companies, 15 employees, 20 intel items
│   │
│   ├── watcher/
│   │   └── web_watcher.py       ← APScheduler 60s intel poller
│   │
│   ├── llm.py                   ← Multi-provider AI utility
│   ├── agent.py                 ← Agentic loop (Anthropic/OpenAI/OpenRouter/Gemini/Ollama)
│   ├── mcp_server.py            ← MCP server exposing all 23 tools
│   └── cli.py                   ← CLI entry point
│
├── frontend/                    ← OSINT Dashboard (React + Vite, port 5173)
│   └── src/
│       ├── components/
│       │   ├── MainDashboard.jsx
│       │   ├── IntelFeed.jsx
│       │   ├── CompanyList.jsx
│       │   ├── CompanyDrilldown.jsx
│       │   ├── EmployeeLeakTable.jsx
│       │   ├── PostTracker.jsx
│       │   └── ThreatBadge.jsx
│       └── App.jsx
│
├── marketing/                   ← Marketing Module (Node.js)
│   ├── src/
│   │   ├── api/                 ← Express REST server (port 3002)
│   │   └── agents/              ← AI content generators
│   └── frontend-app/            ← Marketing Dashboard (React + Vite, port 5174)
│
├── API_INTEGRATION.md           ← Integration contract between modules
├── ROADMAP.md
├── TODO.md
└── pyproject.toml
```

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|---|---|---|
| Python | 3.10 | OSINT core backend |
| Node.js | 18 | Frontend dev servers + Marketing module |
| npm | 8 | JS package management |

**Optional external binaries** (needed for specific OSINT tools):

```bash
pip install holehe              # email footprint enumeration
pip install sherlock-project    # username search across 300+ platforms
pip install sublist3r           # subdomain enumeration
# phoneinfoga — see https://github.com/sundowndev/phoneinfoga/releases
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/LakshmanS27/SQ1INT.git
cd SQ1INT
```

### 2. Configure your `.env` file

Copy the template and fill in your keys:

```bash
cp .env .env.local   # or edit .env directly
```

```env
# ── AI backend — only ONE of the four keys below is required ──────────────
# The platform auto-detects which provider is configured.
# Priority: Anthropic → OpenAI → OpenRouter → Gemini

# 1) Anthropic Claude (recommended)
ANTHROPIC_API_KEY=sk-ant-...

# 2) OpenAI or any OpenAI-compatible endpoint
# OPENAI_API_KEY=sk-...
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# 3) OpenRouter — access to 200+ hosted models
# OPENROUTER_API_KEY=sk-or-...
# OPENROUTER_MODEL=openai/gpt-4o-mini

# 4) Google Gemini
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-1.5-flash
# ─────────────────────────────────────────────────────────────────────────

# Optional — data breach checks
HIBP_API_KEY=your_key

# Optional — IP intelligence
IPINFO_TOKEN=your_token
IP2LOCATION_API_KEY=your_key

# Optional — threat intel sources
SHODAN_API_KEY=your_key
VIRUSTOTAL_API_KEY=your_key
CENSYS_API_ID=your_id
CENSYS_SECRET=your_secret
ABUSEIPDB_API_KEY=your_key

# Optional — GitHub (raises rate limit 60 → 5000 req/h)
GITHUB_TOKEN=your_token

# Optional — Bright Data (live SERP + web scraping)
BRIGHTDATA_API_KEY=your_key
BRIGHTDATA_SERP_ZONE=serp_api1
BRIGHTDATA_UNLOCKER_ZONE=web_unlocker1
```

**Where to get keys:**

| Key | URL |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey |
| `HIBP_API_KEY` | https://haveibeenpwned.com/API/Key |
| `IPINFO_TOKEN` | https://ipinfo.io/account |
| `SHODAN_API_KEY` | https://account.shodan.io |
| `VIRUSTOTAL_API_KEY` | https://www.virustotal.com/gui/my-apikey |
| `ABUSEIPDB_API_KEY` | https://www.abuseipdb.com/account/api |
| `GITHUB_TOKEN` | https://github.com/settings/tokens |

### 3. Install Python dependencies

```bash
# Install core + all optional extras (recommended)
pip install -e ".[all]"

# Or install only what you need:
pip install -e ".[gemini]"      # + Google Gemini support
pip install -e ".[openrouter]"  # + OpenRouter support (uses openai SDK)
pip install -e ".[ollama]"      # + local Ollama support
pip install -e ".[shodan]"      # + Shodan
pip install -e ".[censys]"      # + Censys
```

### 4. Install OSINT Dashboard dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Install Marketing Module dependencies

```bash
cd marketing
npm install
cd ..
```

---

## Running the Platform

Open **four terminal windows**, all from the repo root.

### Terminal 1 — OSINT API

```bash
python -m uvicorn openosint.api.main:app --reload --port 8000
```

On first startup the API automatically:
- Seeds the database with 5 demo companies, 15 employees, and 20 intel items
- Starts the background watcher (polls NVD + CISA every 60 seconds)

Verify it's running:

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"sq1-osint","version":"1.0.0"}
```

### Terminal 2 — OSINT Dashboard

```bash
cd frontend

# Windows
node node_modules\vite\bin\vite.js

# macOS / Linux
npm run dev
```

Open **http://localhost:5173**

### Terminal 3 — Marketing API

```bash
cd marketing
npm run dev:api
```

Runs on **http://localhost:3002**

### Terminal 4 — Marketing Dashboard

```bash
cd marketing
npm run dev:ui
```

Open **http://localhost:5174**

---

## AI Providers

The platform supports four AI backends. Only one key is required. The provider is auto-detected from env vars in priority order, or you can force one with `--provider`.

| Provider | Key | Default model | Notes |
|---|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` | Recommended — native tool-use |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` | Any OpenAI-compatible endpoint |
| OpenRouter | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` | 200+ models via one key |
| Gemini | `GEMINI_API_KEY` | `gemini-1.5-flash` | Google's Gemini SDK |

**Override from the CLI:**

```bash
openosint --provider openrouter --openrouter-model anthropic/claude-3-5-sonnet
openosint --provider gemini --gemini-model gemini-1.5-pro
openosint --provider openai --openai-base-url http://localhost:4000/v1 --openai-model gpt-4o-mini
openosint --provider ollama --ollama-model llama3.2
```

**Detection also applies to `detect_misinfo`** — whichever key is set in `.env` is used automatically for misinformation analysis, no code changes required.

---

## CLI Usage

All OSINT tools are accessible from the command line without a browser:

```bash
# Interactive REPL (default — starts with whichever provider key is set)
openosint

# Force a specific AI provider for the REPL
openosint --provider gemini
openosint --provider openrouter

# Fetch live threat intelligence from NVD + CISA
openosint intel --query "ransomware" --type VULNERABILITY --limit 10

# Full company OSINT scan
openosint company example.com --name "Acme Corp" --email admin@example.com

# Detect misinformation in a claim or article
openosint misinfo "All VPNs have been compromised" --source https://example.com

# Track who else posted a cybersecurity story on Reddit
openosint track "LockBit ransomware targets healthcare" --cve CVE-2024-1234

# Email footprint enumeration (holehe)
openosint email target@example.com

# Username search across 300+ platforms (sherlock)
openosint username johndoe99

# Subdomain enumeration (sublist3r)
openosint domain example.com

# Shodan host lookup
openosint shodan 1.2.3.4

# DNS record audit + misconfig detection
openosint dns example.com

# AbuseIPDB reputation check
openosint abuseipdb 1.2.3.4

# GitHub user + commit email search
openosint github johndoe99

# Structured JSON output from any command
openosint intel --query "zero-day" --json
```

---

## OSINT API Reference

Base URL: `http://localhost:8000`

### Health check

```
GET /health
```
```json
{"status": "ok", "service": "sq1-osint", "version": "1.0.0"}
```

---

### Intelligence Feed

| Endpoint | Description |
|---|---|
| `GET /api/intel/latest?limit=10` | Latest intel items |
| `GET /api/intel/search?q=ransomware` | Keyword search |
| `GET /api/intel/by-type/{type}` | Filter by classification |
| `GET /api/intel/unmarketed` | Items not yet used in marketing |
| `POST /api/intel/{id}/mark-used` | Mark item as used in marketing |
| `POST /api/intel/scan?query=apache` | Trigger a fresh live scan |

Valid classification types: `VULNERABILITY` · `THREAT` · `COMPLIANCE` · `BREACH` · `MISINFORMATION`

---

### Companies

| Endpoint | Description |
|---|---|
| `GET /api/companies` | List all companies |
| `GET /api/companies/{id}` | Get a single company |
| `POST /api/companies` | Add a new company |
| `POST /api/companies/{id}/scan` | Run full OSINT scan (WHOIS + subdomains + dorks + breach) |

**Add a company:**
```json
POST /api/companies
{
  "name": "Acme Corp",
  "domain": "acme.com",
  "contactEmail": "admin@acme.com",
  "tags": ["finance", "saas"]
}
```

---

### Employees

| Endpoint | Description |
|---|---|
| `GET /api/employees/{company_id}` | List employees for a company |
| `POST /api/employees/{company_id}/scan` | Breach scan all employees (HIBP rate-limited) |
| `POST /api/employees/scan-email` | Scan a single email address |

---

### Post Tracker

```
GET /api/tracker/posts?story=lockbit+targets+healthcare&cve=CVE-2024-1234
```

---

## Intel Item Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Critical RCE in Apache HTTP Server",
  "classification": "VULNERABILITY",
  "severity": "CRITICAL",
  "summary": "A remote code execution vulnerability...",
  "cveIds": ["CVE-2024-38476"],
  "tags": ["apache", "rce", "web"],
  "timestamp": "2026-06-12T07:10:00Z",
  "sourceVerified": true,
  "isMisinformation": false,
  "usedInMarketing": false,
  "source": "nvd.nist.gov"
}
```

---

## MCP Server

All 23 OSINT tools are exposed as MCP (Model Context Protocol) tools, letting Claude Code or Claude Desktop call them natively.

**Configure in your MCP settings:**

```json
{
  "mcpServers": {
    "sq1-osint": {
      "command": "python",
      "args": ["-m", "openosint.mcp_server"],
      "cwd": "/path/to/SQ1INT"
    }
  }
}
```

**Available MCP tools:**

| Tool | What it does |
|---|---|
| `search_intel` | NVD CVEs + CISA KEV live feed |
| `validate_source` | Source credibility whitelist check |
| `detect_misinfo` | AI misinfo detection (auto-selects provider) |
| `scan_company` | Full company OSINT orchestrator |
| `track_post` | Reddit competitor post tracker |
| `search_breach` | HaveIBeenPwned v3 breach check |
| `search_email` | holehe email → services footprint |
| `search_username` | sherlock 300+ platform search |
| `search_domain` | sublist3r subdomain enumeration |
| `search_whois` | WHOIS registration data |
| `search_ip` | ipinfo.io geolocation + ASN |
| `search_paste` | psbdmp.ws paste dump search |
| `search_phone` | phoneinfoga carrier + geo |
| `generate_dorks` | Google dork URL generator |
| `search_dns` | DNS records + SPF/DMARC audit |
| `search_shodan` | Shodan host/banner search |
| `search_virustotal` | VirusTotal 70+ AV engine check |
| `search_censys` | Censys internet scan data |
| `search_abuseipdb` | AbuseIPDB abuse reputation |
| `search_github` | GitHub profile + commit email search |
| `search_ip2location` | VPN/Tor/datacenter/proxy detection |
| `search_dorks_live` | Live Google SERP via Bright Data |
| `scrape_url` | Cloudflare-bypassing web scraper |

---

## Module Integration

The Marketing Module reads intelligence from the OSINT API and marks items as used after generating content:

```
OSINT API   →  GET  /api/intel/unmarketed      →  Marketing ingests items
Marketing   →  POST /api/intel/{id}/mark-used  →  Item flagged as marketed
```

The Marketing Dashboard (port 5174) proxies OSINT calls through `/osint/*`, which Vite rewrites to `http://localhost:8000/api/*`.

Full integration contract: [API_INTEGRATION.md](API_INTEGRATION.md)

---

## Environment Variables

### OSINT Core (`.env` in repo root)

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | One of four | Anthropic Claude AI |
| `OPENAI_API_KEY` | One of four | OpenAI or compatible endpoint |
| `OPENROUTER_API_KEY` | One of four | OpenRouter gateway |
| `GEMINI_API_KEY` | One of four | Google Gemini |
| `OPENAI_BASE_URL` | No | Custom OpenAI-compat base URL |
| `OPENAI_MODEL` | No | OpenAI model override |
| `OPENROUTER_MODEL` | No | OpenRouter model slug |
| `GEMINI_MODEL` | No | Gemini model override |
| `HIBP_API_KEY` | No | HaveIBeenPwned breach checks |
| `IPINFO_TOKEN` | No | IP geolocation |
| `SHODAN_API_KEY` | No | Shodan host intelligence |
| `VIRUSTOTAL_API_KEY` | No | VirusTotal reputation checks |
| `CENSYS_API_ID` | No | Censys internet scan data |
| `CENSYS_SECRET` | No | Censys secret key |
| `ABUSEIPDB_API_KEY` | No | AbuseIPDB reputation |
| `GITHUB_TOKEN` | No | GitHub API (raises rate limit) |
| `BRIGHTDATA_API_KEY` | No | Live SERP + web scraping |
| `BRIGHTDATA_SERP_ZONE` | No | Bright Data SERP zone name |
| `BRIGHTDATA_UNLOCKER_ZONE` | No | Bright Data web unlocker zone |
| `IP2LOCATION_API_KEY` | No | VPN/Tor/proxy detection |

### Marketing Module (`marketing/.env`)

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude AI for content generation |
| `PORT` | Marketing API port (default: 3002) |
| `MARKETING_DB_PATH` | Lowdb file path (default: `./.runtime/db.json`) |

---

## Tech Stack

### OSINT Core
| | |
|---|---|
| **Runtime** | Python 3.10+ |
| **API framework** | FastAPI + Uvicorn |
| **Database** | TinyDB (JSON file) |
| **Scheduling** | APScheduler |
| **HTTP client** | httpx (async) |
| **AI** | Anthropic · OpenAI · OpenRouter · Gemini |
| **Protocol** | MCP (Model Context Protocol) |

### OSINT Dashboard
| | |
|---|---|
| **UI framework** | React 18 |
| **Build tool** | Vite 5 |
| **Styling** | Tailwind CSS |
| **Charts** | Recharts |
| **Icons** | lucide-react |
| **Routing** | react-router-dom |

### Marketing Module
| | |
|---|---|
| **Runtime** | Node.js 18+ |
| **API framework** | Express |
| **Database** | Lowdb (JSON file) |
| **AI** | @anthropic-ai/sdk |
| **Video** | Remotion |
| **Email** | nodemailer |
| **Testing** | Vitest |

---

## License

MIT — see [LICENSE](LICENSE).

For security research and authorized use only. See [DISCLAIMER.md](DISCLAIMER.md).
