# Product: Unified Multimedia Platform

A monorepo consolidating two cybersecurity tools into a single integrated platform with two microservices and two React dashboards.

## Core Products

### Intelligence Service (Python/FastAPI)
Migrated from `zero_day_radar/`. A Cyber Threat Intelligence (CTI) platform that:
- Continuously collects security signals from 50+ sources: social (X/Twitter via Nitter, Reddit, LinkedIn, HackerNews), vendor advisories (MSRC, Cisco, Fortinet, Palo Alto, VMware), researcher blogs (Project Zero, Unit42, Krebs, DFIR Report), vulnerability databases (CVE Program, NVD, CISA KEV, GitHub PoC, Exploit-DB, Metasploit), and compliance sources (NIST, ISO, PCI DSS, GDPR, EU AI Act)
- Scores all intelligence on a 0–100 SAINT scale (LOW / MEDIUM / HIGH / VERY_HIGH / CRITICAL) using source credibility weighting + corroboration bonuses
- Uses Ollama (local LLM) to cluster raw signals by vendor/product/CVE and produce enriched `unified_intel` entries
- Exposes a REST API consumed by the Security Dashboard and Content Service

### Content Service (Node.js/TypeScript)
Migrated from `OpenOSINT/marketing/`. Converts raw intel into campaign-ready content:
- AI-generated email campaigns, HyperFrame visuals (1200×628px PNG), Remotion video compositions, Slack Block Kit messages, Teams Adaptive Cards, LinkedIn posts
- Human approval workflow: all generated assets must pass `pending_review → approved → published` before distribution
- LinkedIn OAuth 2.0 integration for posting

### Security Dashboard (React)
Used by security analysts. Displays live intel feed, SAINT score breakdowns, source management, and background job controls.

### Marketing Dashboard (React)
Used by the marketing team. Shows unmarketed intel queue, content generation interfaces, approval queue, asset gallery, and subscriber management.

## Key Business Rules
- Content is only generated from real intelligence items — if Intelligence Service is unreachable, content generation returns an error
- Every generated asset creates a `content_assets` record with `status = pending_review`; no publish action succeeds without `status = approved`
- After content is created from an intel item, `used_in_marketing = true` is set on `unified_intel` via cross-service PATCH call (retried up to 3× with exponential backoff)
- JWT-based RBAC: `security_team` role accesses Intelligence Service endpoints; `marketing_team` role accesses Content Service endpoints
