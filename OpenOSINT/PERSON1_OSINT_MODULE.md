# 🛡️ SQ1 OSINT Intelligence Platform — PERSON 1: Core OSINT Module
### Claude Build Prompt | Fork of OpenOSINT v2.1.0 | Deadline: 14:40

---

## ⚡ WHAT YOU ARE DOING

You are **forking and extending `https://github.com/OpenOSINT/OpenOSINT`** — a Python MCP-native OSINT framework — and repurposing it into **SQ1 OSINT**: a cybersecurity threat intelligence platform with a web dashboard.

**Do NOT build from scratch.** Clone the repo, understand the existing architecture, then add on top.

**Start time:** 11:40 | **Hard deadline:** 14:40 | **Your budget:** 180 min

---

## 🔍 UNDERSTAND OPENOSINT FIRST (READ BEFORE CODING)

OpenOSINT's 3-layer architecture (never violate layer boundaries):

```
openosint/tools/        ← Stateless async functions. No UI, no MCP, no imports upward.
openosint/mcp_server.py ← Registers tools as MCP schemas. Calls tools/. No CLI logic.
openosint/cli.py        ← Human-facing CLI. Calls tools/ directly.
```

**9 tools already built and working — REUSE ALL OF THEM:**

| Existing Tool | File | What it does | You'll use it for |
|---|---|---|---|
| `search_breach` | `tools/search_breach.py` | HaveIBeenPwned v3 API | Employee dark web scan ✅ |
| `search_email` | `tools/search_email.py` | holehe — email → services | Employee footprint ✅ |
| `search_username` | `tools/search_username.py` | sherlock — 300+ platforms | Employee account tracking ✅ |
| `search_paste` | `tools/search_paste.py` | psbdmp.ws — pastebin dumps | Employee data leaks ✅ |
| `search_domain` | `tools/search_domain.py` | sublist3r — subdomains | Company attack surface ✅ |
| `search_whois` | `tools/search_whois.py` | WHOIS data | Company registration info ✅ |
| `search_ip` | `tools/search_ip.py` | ipinfo.io — IP intel | Company infrastructure ✅ |
| `generate_dorks` | `tools/generate_dorks.py` | Google dork URLs | Company exposure ✅ |
| `search_phone` | `tools/search_phone.py` | phoneinfoga | Employee phone intel ✅ |

---

## 🆕 WHAT YOU ARE ADDING

### New Tools (add to `openosint/tools/`)
5 new Python async tool files following the exact same pattern as existing tools:

1. **`search_intel.py`** — Fetches CVEs from NVD, alerts from CISA RSS, news from trusted security sources
2. **`validate_source.py`** — Whitelist check + Claude-assisted validation for unknown sources
3. **`detect_misinfo.py`** — Claude-powered fake cybersecurity news detector
4. **`scan_company.py`** — Orchestrates existing tools (whois + domain + breach + dorks) for full company scan
5. **`track_post.py`** — Checks if same story was posted by others via Reddit + NewsAPI, returns post dates + engagement

### New Layers (add as new directories)
- **`openosint/api/`** — FastAPI REST server (port 8000) so the React frontend and Person 2 can call your tools via HTTP
- **`openosint/watcher/`** — Background polling agent (runs every 60s, calls `search_intel`, pushes to DB)
- **`openosint/data/`** — TinyDB JSON store for intel items, companies, employees
- **`frontend/`** — React + Vite dashboard (separate from the Python package)

### Extended Files
- **`openosint/mcp_server.py`** — Register the 5 new tools as MCP tools
- **`openosint/cli.py`** — Add new CLI commands: `openosint intel`, `openosint company`, `openosint watch`
- **`pyproject.toml`** — Add new dependencies: fastapi, uvicorn, tinydb, httpx, anthropic, apscheduler

---

## 📁 FINAL REPO STRUCTURE (after your changes)

```
sq1-openosint/                         ← Your fork, renamed
├── openosint/
│   ├── tools/
│   │   ├── search_email.py            ← EXISTING — DO NOT MODIFY
│   │   ├── search_username.py         ← EXISTING — DO NOT MODIFY
│   │   ├── search_breach.py           ← EXISTING — DO NOT MODIFY
│   │   ├── search_whois.py            ← EXISTING — DO NOT MODIFY
│   │   ├── search_ip.py               ← EXISTING — DO NOT MODIFY
│   │   ├── search_domain.py           ← EXISTING — DO NOT MODIFY
│   │   ├── generate_dorks.py          ← EXISTING — DO NOT MODIFY
│   │   ├── search_paste.py            ← EXISTING — DO NOT MODIFY
│   │   ├── search_phone.py            ← EXISTING — DO NOT MODIFY
│   │   ├── exceptions.py              ← EXISTING — DO NOT MODIFY
│   │   │
│   │   ├── search_intel.py            ← NEW ✨
│   │   ├── validate_source.py         ← NEW ✨
│   │   ├── detect_misinfo.py          ← NEW ✨
│   │   ├── scan_company.py            ← NEW ✨
│   │   └── track_post.py              ← NEW ✨
│   │
│   ├── api/                           ← NEW ✨
│   │   ├── __init__.py
│   │   ├── main.py                    ← FastAPI app entry, CORS, routes
│   │   └── routes/
│   │       ├── intel.py               ← /api/intel/*
│   │       ├── companies.py           ← /api/companies/*
│   │       ├── employees.py           ← /api/employees/*
│   │       └── tracker.py             ← /api/tracker/*
│   │
│   ├── watcher/                       ← NEW ✨
│   │   └── web_watcher.py             ← APScheduler background poller
│   │
│   ├── data/                          ← NEW ✨
│   │   ├── store.py                   ← TinyDB wrapper
│   │   └── seed.py                    ← Seed demo data
│   │
│   ├── mcp_server.py                  ← EXISTING — EXTEND with new tools
│   └── cli.py                         ← EXISTING — EXTEND with new commands
│
├── frontend/                          ← NEW ✨ (React dashboard)
│   ├── src/
│   │   ├── components/
│   │   │   ├── MainDashboard.jsx
│   │   │   ├── IntelFeed.jsx
│   │   │   ├── CompanyList.jsx
│   │   │   ├── CompanyDrilldown.jsx
│   │   │   ├── EmployeeLeakTable.jsx
│   │   │   ├── PostTracker.jsx
│   │   │   └── ThreatBadge.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Companies.jsx
│   │   │   ├── CompanyDetail.jsx
│   │   │   └── Employees.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── .env                               ← NEW ✨
├── ROADMAP.md                         ← CREATE FIRST ✨
├── TODO.md                            ← CREATE FIRST ✨
├── API_INTEGRATION.md                 ← CREATE FOR PERSON 2 ✨
├── pyproject.toml                     ← EXISTING — UPDATE deps
└── README.md                          ← UPDATE
```

---

## 🚀 PHASE 1 — SETUP (15 min | 11:40–11:55)

```bash
# 1. Clone and rename
git clone https://github.com/OpenOSINT/OpenOSINT.git sq1-openosint
cd sq1-openosint

# 2. Install existing deps
pip install -e .
pip install holehe sherlock-project sublist3r

# 3. Add new Python deps
pip install fastapi uvicorn tinydb httpx anthropic apscheduler python-dotenv

# 4. Set up frontend
mkdir frontend && cd frontend
npm create vite@latest . -- --template react
npm install
npm install tailwindcss @tailwindcss/vite recharts lucide-react
cd ..

# 5. Create .env
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_key_here
HIBP_API_KEY=your_key_here
IPINFO_TOKEN=your_key_here
NEWS_API_KEY=your_key_here
PORT=8000
EOF
```

**Immediately after setup — create tracking files:**

```bash
touch ROADMAP.md TODO.md API_INTEGRATION.md
```

Fill in the templates at the bottom of this document.

---

## 🔧 PHASE 2 — NEW PYTHON TOOLS (40 min | 11:55–12:35)

Follow the **exact pattern** of existing tools. Look at `openosint/tools/search_breach.py` as your template before writing anything.

### `openosint/tools/search_intel.py`

```python
"""
search_intel — Fetch CVEs, CISA alerts, and security news from trusted sources.
"""
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

TRUSTED_SOURCES = [
    "nvd.nist.gov", "cisa.gov", "krebsonsecurity.com", "bleepingcomputer.com",
    "thehackernews.com", "darkreading.com", "threatpost.com", "securityweek.com"
]

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_RSS = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

async def search_intel(query: str = "", classification: str = "ALL", limit: int = 10) -> str:
    """
    Fetch cybersecurity intelligence from NVD and CISA.
    classification: ALL | VULNERABILITY | THREAT | COMPLIANCE | BREACH
    Returns formatted string of intel items.
    """
    results = []
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Fetch from NVD
        try:
            params = {"resultsPerPage": limit, "keywordSearch": query or "critical"}
            resp = await client.get(NVD_API, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for vuln in data.get("vulnerabilities", [])[:5]:
                    cve = vuln.get("cve", {})
                    cve_id = cve.get("id", "Unknown")
                    desc = cve.get("descriptions", [{}])[0].get("value", "No description")
                    severity = "UNKNOWN"
                    metrics = cve.get("metrics", {})
                    if "cvssMetricV31" in metrics:
                        severity = metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
                    results.append(f"[CVE][{severity}] {cve_id}: {desc[:200]}")
        except Exception as e:
            results.append(f"[NVD ERROR] {str(e)}")
        
        # Fetch from CISA KEV
        try:
            resp = await client.get(CISA_RSS)
            if resp.status_code == 200:
                kev = resp.json()
                vulns = kev.get("vulnerabilities", [])[-5:]
                for v in vulns:
                    results.append(f"[CISA KEV][CRITICAL] {v.get('cveID')}: {v.get('vulnerabilityName')} — Due: {v.get('dueDate')}")
        except Exception as e:
            results.append(f"[CISA ERROR] {str(e)}")
    
    if not results:
        return "No intel found for given parameters."
    
    output = f"Intelligence results ({len(results)} items):\n\n"
    output += "\n".join(f"[+] {r}" for r in results)
    return output
```

### `openosint/tools/validate_source.py`

```python
"""
validate_source — Check if a URL/domain is a trusted security source.
Uses whitelist first, then Claude for unknowns.
"""
import re
from urllib.parse import urlparse

TRUSTED_DOMAINS = {
    "nvd.nist.gov", "cisa.gov", "krebsonsecurity.com", "bleepingcomputer.com",
    "thehackernews.com", "darkreading.com", "threatpost.com", "securityweek.com",
    "haveibeenpwned.com", "exploit-db.com", "cert.gov", "us-cert.gov",
    "schneier.com", "portswigger.net", "sans.org", "mitre.org"
}

KNOWN_DISINFO = {
    "infowars.com", "naturalnews.com", "zerohedge.com"
}

async def validate_source(url: str) -> str:
    """
    Validate whether a source URL is trusted for cybersecurity intelligence.
    Returns: TRUSTED | UNTRUSTED | SUSPICIOUS | UNKNOWN
    """
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        domain = parsed.netloc.lower().lstrip("www.")
    except Exception:
        return f"INVALID — Could not parse URL: {url}"
    
    if domain in TRUSTED_DOMAINS:
        return f"TRUSTED — {domain} is a verified cybersecurity intelligence source."
    
    if domain in KNOWN_DISINFO:
        return f"SUSPICIOUS — {domain} is known for misinformation. Do not surface this intel."
    
    # Heuristic checks for unknown domains
    gov_or_edu = domain.endswith(".gov") or domain.endswith(".edu")
    if gov_or_edu:
        return f"LIKELY_TRUSTED — {domain} is a government or academic domain."
    
    return f"UNKNOWN — {domain} is not in trusted whitelist. Verify manually before surfacing."
```

### `openosint/tools/detect_misinfo.py`

```python
"""
detect_misinfo — Use Claude to detect cybersecurity misinformation.
"""
import os
import asyncio
import anthropic

SYSTEM_PROMPT = """You are a cybersecurity fact-checker for SQ1 OSINT.
Analyze the provided claim or article and determine if it contains misinformation.

Return ONLY a JSON object (no markdown):
{
  "verdict": "LEGITIMATE | MISINFORMATION | UNVERIFIED",
  "confidence": 0.0-1.0,
  "reasoning": "2-3 sentence explanation",
  "red_flags": ["list", "of", "suspicious", "elements"],
  "recommended_action": "SURFACE | SUPPRESS | FLAG_FOR_REVIEW"
}"""

async def detect_misinfo(content: str, source_url: str = "") -> str:
    """
    Use Claude to detect if cybersecurity content is misinformation.
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    
    user_message = f"""Analyze this cybersecurity claim for misinformation:

Source: {source_url or 'Not provided'}
Content: {content[:2000]}

Respond with the JSON schema only."""
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return message.content[0].text
    except Exception as e:
        return f'{{"verdict": "ERROR", "reasoning": "{str(e)}"}}'
```

### `openosint/tools/scan_company.py`

```python
"""
scan_company — Full company OSINT scan orchestrating existing tools.
"""
import asyncio
from openosint.tools.search_whois import search_whois
from openosint.tools.search_domain import search_domain
from openosint.tools.generate_dorks import generate_dorks
from openosint.tools.search_breach import search_breach

async def scan_company(company_name: str, domain: str, contact_email: str = "") -> str:
    """
    Run a full company OSINT scan using existing OpenOSINT tools.
    Combines: WHOIS + subdomain enumeration + Google dorks + breach check.
    """
    results = [f"=== Company OSINT Scan: {company_name} ({domain}) ===\n"]
    
    # Run all scans concurrently
    tasks = [
        search_whois(domain),
        search_domain(domain),
        generate_dorks(domain),
    ]
    
    if contact_email:
        tasks.append(search_breach(contact_email))
    
    scan_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    labels = ["WHOIS", "SUBDOMAINS", "DORKS"]
    if contact_email:
        labels.append("BREACH_CHECK")
    
    for label, result in zip(labels, scan_results):
        if isinstance(result, Exception):
            results.append(f"\n[{label}] ERROR: {result}")
        else:
            results.append(f"\n[{label}]\n{result}")
    
    return "\n".join(results)
```

### `openosint/tools/track_post.py`

```python
"""
track_post — Check if a cybersecurity story was posted by others (competitors/individuals).
"""
import asyncio
import httpx
from datetime import datetime

REDDIT_API = "https://www.reddit.com/search.json"
HEADERS = {"User-Agent": "SQ1-OSINT-Bot/1.0"}

async def track_post(story_title: str, cve_id: str = "") -> str:
    """
    Search Reddit and news for the same story.
    Returns who posted it, when, and their engagement.
    """
    results = []
    query = cve_id if cve_id else story_title[:80]
    
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        # Reddit search
        try:
            params = {
                "q": query,
                "sort": "new",
                "limit": 5,
                "restrict_sr": "false",
                "type": "link"
            }
            resp = await client.get(REDDIT_API, params=params)
            if resp.status_code == 200:
                posts = resp.json().get("data", {}).get("children", [])
                for post in posts:
                    d = post.get("data", {})
                    created = datetime.utcfromtimestamp(d.get("created_utc", 0)).strftime("%Y-%m-%d %H:%M UTC")
                    results.append(
                        f"[Reddit][r/{d.get('subreddit')}] "
                        f"Posted: {created} | "
                        f"Score: {d.get('score', 0)} | "
                        f"Comments: {d.get('num_comments', 0)} | "
                        f"Author: u/{d.get('author', 'unknown')} | "
                        f"URL: {d.get('url', '')[:80]}"
                    )
        except Exception as e:
            results.append(f"[Reddit ERROR] {str(e)}")
    
    if not results:
        return f"No competing posts found for: {query}"
    
    output = f"Competitor post tracking for '{query}':\n\n"
    output += "\n".join(f"[+] {r}" for r in results)
    return output
```

---

## ⚙️ PHASE 3 — FASTAPI REST LAYER (25 min | 12:35–13:00)

```python
# openosint/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openosint.api.routes import intel, companies, employees, tracker
from openosint.watcher.web_watcher import start_watcher
import asyncio

app = FastAPI(title="SQ1 OSINT API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Person 2's port too
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intel.router, prefix="/api/intel")
app.include_router(companies.router, prefix="/api/companies")
app.include_router(employees.router, prefix="/api/employees")
app.include_router(tracker.router, prefix="/api/tracker")

@app.on_event("startup")
async def startup():
    asyncio.create_task(start_watcher())

@app.get("/health")
def health():
    return {"status": "ok", "service": "sq1-osint"}
```

Key routes to build:

```python
# openosint/api/routes/intel.py
# GET  /api/intel/latest          → last 10 intel items from DB
# GET  /api/intel/search?q=...    → search intel by keyword
# GET  /api/intel/by-type/{type}  → filter THREAT|BREACH|COMPLIANCE|VULNERABILITY|MISINFO
# GET  /api/intel/unmarketed      → items not yet sent to marketing
# POST /api/intel/{id}/mark-used  → Person 2 marks item as marketed
# POST /api/intel/scan            → trigger fresh scan (calls search_intel)

# openosint/api/routes/companies.py
# GET  /api/companies             → all companies
# GET  /api/companies/{id}        → single company
# POST /api/companies             → add new company
# POST /api/companies/{id}/scan   → trigger scan_company for this company

# openosint/api/routes/employees.py
# GET  /api/employees/{company_id}         → employee list
# POST /api/employees/{company_id}/scan    → breach scan all employees (search_breach)
# POST /api/employees/scan-email           → scan single email

# openosint/api/routes/tracker.py
# GET  /api/tracker/posts?story=...        → track_post results
```

Run the API:
```bash
uvicorn openosint.api.main:app --reload --port 8000
```

---

## 🖥️ PHASE 4 — REACT DASHBOARD (45 min | 13:00–13:45)

```bash
cd frontend
npm run dev  # runs on port 5173
```

**Vite config — proxy to FastAPI:**
```javascript
// frontend/vite.config.js
export default {
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
}
```

### Component Build Order

1. **`MainDashboard.jsx`** — 4 stat cards + live intel feed
   - Stats: Total Intel Today, Critical CVEs, Companies Monitored, Dark Web Hits
   - Poll `GET /api/intel/latest` every 30s
   
2. **`IntelFeed.jsx`** — Cards with severity badge + classification chip
   - Color map: CRITICAL→red, HIGH→orange, MEDIUM→yellow, LOW→cyan, INFO→gray
   - Show: title, summary, CVE IDs, source verified checkmark, timestamp
   - "Create Marketing Asset" button → calls `POST /api/intel/{id}/mark-used` + emits to Person 2

3. **`CompanyList.jsx`** — Grid of company cards
   - Each card: name, domain, threat score (0-100), last scan time, employee count
   - "Scan Now" button → `POST /api/companies/{id}/scan`

4. **`CompanyDrilldown.jsx`** — Full company view
   - Tabs: WHOIS | Subdomains | Employee Leaks | Dorks | Intel Feed
   - Shows breach history timeline (chart)

5. **`EmployeeLeakTable.jsx`** — Table: email, services found (holehe), paste mentions, breach count
   - "Scan" button per employee → `POST /api/employees/scan-email`
   - Color code severity: red if in HIBP breach, orange if in paste

6. **`PostTracker.jsx`** — Table: story title → who else posted → date → engagement
   - Columns: Platform, Author/Sub, Posted, Score, Comments, Link

---

## 📡 PHASE 5 — MCP SERVER EXTENSION (15 min | 13:45–14:00)

Extend `openosint/mcp_server.py` to register your 5 new tools.

Follow the **exact pattern** of the existing tool registrations in mcp_server.py. Look at how `search_breach` is registered and copy that pattern for each new tool:

```python
# Add these 5 tool registrations in mcp_server.py
# after the existing 9 tools:

# Tool: search_intel
# Tool: validate_source
# Tool: detect_misinfo
# Tool: scan_company
# Tool: track_post
```

Also add CLI commands to `cli.py`:
```bash
openosint intel [--query TEXT] [--type CLASSIFICATION]
openosint company DOMAIN [--email CONTACT_EMAIL]
openosint misinfo "content to check" [--source URL]
openosint track "story title" [--cve CVE-ID]
```

---

## 🎨 UI DESIGN SYSTEM

```css
/* Dark cyberpunk SOC theme */
--bg-primary:    #0a0e1a;   /* main background */
--bg-secondary:  #0f1629;   /* sidebar */
--bg-card:       #141d35;   /* cards */
--accent-cyan:   #00d4ff;   /* primary actions, LIVE badge */
--accent-green:  #00ff88;   /* verified, clean, MCP */
--accent-red:    #ff3366;   /* CRITICAL, breach */
--accent-orange: #ff6600;   /* HIGH */
--accent-yellow: #ffcc00;   /* MEDIUM, COMPLIANCE */
--text-primary:  #e2e8f0;
--text-muted:    #64748b;
--border:        #1e3a5f;
--font-mono:     'IBM Plex Mono', monospace;  /* data values */
```

- Animated pulsing green dot for "LIVE" web watcher status
- Glowing red border on CRITICAL intel cards
- Monospace for CVE IDs, timestamps, IP addresses

---

## 📄 ROADMAP.md — CREATE THIS FIRST

```markdown
# SQ1 OSINT Core — Roadmap
## Hackathon MVP (due 14:40)
- [x] Forked OpenOSINT v2.1.0
- [ ] New tool: search_intel (NVD + CISA)
- [ ] New tool: validate_source
- [ ] New tool: detect_misinfo (Claude)
- [ ] New tool: scan_company (orchestrator)
- [ ] New tool: track_post (Reddit)
- [ ] FastAPI REST layer (port 8000)
- [ ] Extended mcp_server.py (+5 tools)
- [ ] React dashboard — Main + Intel feed
- [ ] React dashboard — Company list + drilldown
- [ ] React dashboard — Employee leak table
- [ ] React dashboard — Post tracker
- [ ] API_INTEGRATION.md for Person 2

## Post-Hackathon v2
- Shodan API integration (attack surface)
- Real-time WebSocket push for new intel
- ML-based misinfo confidence scoring
- Multi-tenant auth (companies log in)
- PDF executive report generation
- Alerting thresholds per company
- Tor-based dark web crawling
```

---

## ✅ TODO.md — CREATE THIS FIRST

```markdown
# SQ1 OSINT Core — TODO

## 🔴 P0 — Must Ship (MVP)
- [ ] Clone + install deps (Phase 1)
- [ ] search_intel.py — NVD + CISA feeds
- [ ] validate_source.py — whitelist check
- [ ] detect_misinfo.py — Claude call
- [ ] scan_company.py — orchestrates existing tools
- [ ] FastAPI main.py + all 4 route files
- [ ] TinyDB store.py
- [ ] Main Dashboard UI (stats + intel feed)
- [ ] Company List + Drilldown UI
- [ ] Employee Leak Table UI
- [ ] /api/intel/latest for Person 2
- [ ] API_INTEGRATION.md

## 🟡 P1 — Should Ship If Time
- [ ] track_post.py — Reddit tracker
- [ ] Post Tracker UI component
- [ ] Background web watcher (APScheduler)
- [ ] Extend mcp_server.py with new tools
- [ ] Extend cli.py with new commands

## 🟢 P2 — Nice to Have
- [ ] Animated threat score gauge
- [ ] Real-time poll for new intel
- [ ] Company scan history timeline
- [ ] Export intel as JSON
```

---

## 📋 API_INTEGRATION.md — CREATE FOR PERSON 2

```markdown
# SQ1 OSINT API — Integration Guide for Marketing Module

Base URL: http://localhost:8000

## Endpoints Person 2 should use:

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

## CORS
Allowed origins: http://localhost:5174 (Person 2's Vite port)

## Intel item schema:
{
  "id": "string",
  "title": "string",
  "classification": "VULNERABILITY|THREAT|COMPLIANCE|BREACH|MISINFORMATION",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "summary": "string",
  "cveIds": ["CVE-XXXX-XXXXX"],
  "tags": ["string"],
  "timestamp": "ISO8601",
  "sourceVerified": boolean,
  "isMisinformation": boolean
}
```

---

## ⏱️ TIME & TOKEN ESTIMATE

| Phase | Time | Claude Tokens |
|-------|------|--------------|
| Setup + clone | 15 min | ~3K |
| 5 new Python tools | 40 min | ~25K |
| FastAPI + routes | 25 min | ~20K |
| React frontend | 45 min | ~40K |
| MCP extension + CLI | 15 min | ~10K |
| Debugging + iteration | 40 min | ~35K |
| **Total** | **180 min** | **~133K tokens** |

**Build session cost:** ~$1.50–2.00  
**Runtime per full company scan:** ~8,000 tokens (~$0.08)  
**Runtime per intel fetch:** ~2,000 tokens (~$0.02)

---

## 🚀 RUN COMMANDS

```bash
# Terminal 1 — FastAPI backend
uvicorn openosint.api.main:app --reload --port 8000

# Terminal 2 — React frontend
cd frontend && npm run dev   # port 5173

# Terminal 3 — MCP server (optional, for testing)
python openosint/mcp_server.py

# Terminal 4 — CLI testing
openosint intel --query "ransomware"
openosint company example.com --email admin@example.com
```

---

## ⚠️ CRITICAL RULES

1. **Never modify existing tools** in `openosint/tools/` — add new files only
2. **Respect the 3-layer rule**: tools have no UI, MCP has no CLI logic, CLI has no MCP logic
3. **FastAPI is separate from the 3 layers** — it calls tools/ directly like CLI does
4. **HIBP rate limit**: 1 req per 1,500ms — add `asyncio.sleep(1.6)` between bulk email scans
5. **Claude JSON responses**: always wrap `json.loads()` in try/catch, strip markdown fences first
6. **CORS**: must allow `localhost:5174` — Person 2's frontend calls your API
7. **Seed data**: add 5 demo companies + 20 demo intel items + 15 employees in `data/seed.py`
8. **Use `claude-sonnet-4-6`** in detect_misinfo.py — not older models

Good luck. Fork. Extend. Ship. 🛡️
