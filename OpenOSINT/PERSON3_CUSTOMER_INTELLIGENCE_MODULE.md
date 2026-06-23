# SQ1 OSINT Intelligence Platform - PERSON 3: Customer Intelligence Module
### Claude Build Prompt | Agent 9 | Fits Between Person 1 OSINT Core and Person 2 Marketing Module | Deadline: 14:40

---

## WHAT YOU ARE DOING

You are building **Agent 9 - Customer Intelligence Agent** inside the existing SQ1 Security Intelligence Copilot platform.

This is **not a standalone app**.
This is **not a new repository**.
This is **not a separate dashboard**.

Your job is to add a customer-intelligence layer that turns LinkedIn engagement with SQ1 cybersecurity content into qualified potential customer leads.

Agent 9 sits between:

- **Person 1 - OSINT Core:** provides cybersecurity intelligence, company intelligence, and the main SQ1 dashboard.
- **Person 2 - Marketing Module:** creates emails, visuals, videos, Slack alerts, and Teams alerts from intelligence.
- **Person 3 - Customer Intelligence:** identifies who is engaging with SQ1 content and decides which leads should trigger marketing and sales actions.

---

## SYSTEM ROLE

Agent 9 answers:

- Who engaged with SQ1 cybersecurity content?
- Which company do they belong to?
- Are they a buyer, influencer, or practitioner?
- How engaged are they?
- What is their customer intent score?
- What action should SQ1 take next?

Workflow:

```text
LinkedIn Engagement
-> Profile Discovery
-> Company Identification
-> Engagement Analysis
-> Intent Scoring
-> Lead Classification
-> Marketing Trigger
-> Sales Notification
```

---

## CRITICAL RULES

1. Use **LinkedIn engagement only** as the data source.
2. Do not scrape LinkedIn. Process engagement data supplied to SQ1.
3. Do not modify Person 1 agents or Person 2 agents.
4. Do not create a separate application.
5. Do not create a new dashboard shell.
6. Add only the Agent 9 files listed in this document.
7. Integrate with existing SQ1 APIs and dashboard patterns.
8. Use Company Intelligence Agent data when available.
9. Hot leads should trigger Person 2 marketing/comms hooks.
10. Keep implementation demo-friendly with mockable data and clean APIs.

---

## FILES TO CREATE ONLY

```text
openosint/customer_intelligence/agent.py
openosint/customer_intelligence/models/customer_intelligence.py
openosint/customer_intelligence/services/linkedin_intelligence.py
openosint/customer_intelligence/services/intent_scoring.py
openosint/customer_intelligence/services/lead_classifier.py
openosint/customer_intelligence/integrations/marketing.py
openosint/data/customer_leads.py
openosint/api/routes/customer_intelligence.py
frontend/src/components/CustomerIntelligenceWidget.jsx
Roadmap.md
TODO.md
```

If the repo uses uppercase `ROADMAP.md`, update that file instead of creating a duplicate lowercase roadmap.

If the repo uses uppercase `TODO.md`, update that file instead of creating a duplicate lowercase TODO.

Agent 9 belongs inside Person 1's existing `openosint/` platform package. Do not create root-level `agents/`, `services/`, `models/`, `api/`, or `dashboard/` folders for this module.

Target structure:

```text
openosint/
├── customer_intelligence/
│   ├── __init__.py
│   ├── agent.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── customer_intelligence.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── linkedin_intelligence.py
│   │   ├── intent_scoring.py
│   │   └── lead_classifier.py
│   └── integrations/
│       ├── __init__.py
│       └── marketing.py
├── data/
│   └── customer_leads.py
└── api/
    └── routes/
        └── customer_intelligence.py

frontend/
└── src/
    └── components/
        └── CustomerIntelligenceWidget.jsx
```

---

## DATA SOURCE

LinkedIn engagement only.

Monitor interactions on SQ1 content:

- Threat Intelligence Posts
- Vulnerability Reports
- Breach Reports
- Compliance Updates
- Security Research
- Misinformation Clarifications

Track engagement events:

- Likes
- Comments
- Shares/Reposts
- Follows

---

## PROFILE DISCOVERY

Extract:

- Name
- Company
- Job Title
- Industry
- Seniority
- LinkedIn profile URL or LinkedIn ID when provided

Classify role category:

| Category | Roles |
|---|---|
| Decision Makers | CISO, VP Security, Security Director |
| Influencers | Security Architect, SOC Manager, Compliance Manager |
| Practitioners | Security Engineer, Security Analyst |

---

## ENGAGEMENT ANALYSIS

Track:

- Total Likes
- Total Comments
- Total Shares
- Total Follows
- First Seen
- Last Seen
- Engagement Frequency
- Content categories engaged with
- Intel topics engaged with counts

Detect:

- Repeated engagement
- Consistent engagement
- Long-term engagement
- Multi-category engagement

Track Person 1 intel topics explicitly:

```json
{
  "engaged_categories": ["THREAT", "BREACH", "COMPLIANCE"],
  "engaged_category_counts": {
    "THREAT": 4,
    "BREACH": 2,
    "COMPLIANCE": 1
  }
}
```

Allowed normalized topics:

- `THREAT`
- `VULNERABILITY`
- `BREACH`
- `COMPLIANCE`
- `SECURITY_RESEARCH`
- `MISINFORMATION`

This allows Person 2 to create targeted follow-up campaigns without additional lookups.

---

## INTENT SCORING

Formula:

```text
Intent Score =
Engagement Score +
Decision Power Score +
Company Fit Score
```

Engagement weights:

| Engagement | Score |
|---|---:|
| Like | 1 |
| Comment | 3 |
| Share/Repost | 5 |
| Follow | 5 |

Decision power weights:

| Role | Score |
|---|---:|
| CISO | 25 |
| VP Security | 25 |
| Security Director | 20 |
| SOC Manager | 15 |
| Security Architect | 15 |
| Compliance Manager | 15 |
| Security Engineer | 10 |
| Security Analyst | 10 |

Company fit weights:

| Industry | Score |
|---|---:|
| Government | 25 |
| Banking | 20 |
| Critical Infrastructure | 20 |
| Healthcare | 15 |
| Insurance | 15 |
| Enterprise SaaS | 15 |

---

## LEAD CLASSIFICATION

| Intent Score | Category |
|---:|---|
| 90+ | Hot Lead |
| 70-89 | Warm Lead |
| 50-69 | Interested |
| <50 | Awareness |

---

## REQUIRED OUTPUT

Each analyzed lead must return:

- Lead Profile
- Company ID when matched to Person 1 company intelligence
- Company Domain when available
- Company Threat Score when available
- Engagement Analysis
- Engaged Categories
- Engaged Category Counts
- Intent Score
- Score Breakdown
- Lead Category
- AI Insights
- Recommended Action
- Triggered Integrations

Example:

```text
Hot Lead Detected

Name: John Smith
Role: Security Architect
Company: ABC Bank
Intent Score: 92

AI Insights:
- Engaged with multiple threat intelligence posts
- Security influencer likely to shape vendor evaluation
- High-value industry
- Consistent engagement over time

Recommended Action:
Schedule Security Intelligence Demo
```

---

## INTEGRATION WITH PERSON 1

Person 1 owns:

- `openosint/`
- `frontend/`
- FastAPI on port `8000`
- Company intelligence
- Threat intelligence feed
- Main SQ1 dashboard

Agent 9 should:

- Use Company Intelligence Agent data when available.
- Look up existing company records by company name and domain where possible.
- Store Person 1 company identifiers in the lead profile.
- Expose a FastAPI route file inside Person 1's existing route directory.
- Provide a dashboard widget that Person 1 can import into the existing SQ1 dashboard.
- Persist leads through Person 1's existing data layer.

When Company Intelligence Agent returns a company record, store:

```json
{
  "company_id": "company-001",
  "company_name": "ABC Bank",
  "company_domain": "abcbank.example",
  "company_threat_score": 82,
  "industry": "Banking"
}
```

Do not store only `company_name` when a company ID is available. This prevents duplicate companies and keeps Agent 9 aligned with Person 1's company drilldown views.

Suggested mount:

```python
from openosint.api.routes import customer_intelligence

app.include_router(
    customer_intelligence.router,
    prefix="/api/customer-intelligence",
    tags=["customer-intelligence"],
)
```

Do not modify `openosint/api/main.py` unless explicitly asked.

---

## INTEGRATION WITH PERSON 2

Person 2 owns:

- `marketing/`
- Email Campaign Engine
- HyperFrame Visual Content Generator
- Remotion Video Builder
- Slack and Teams alerts
- Marketing app on port `5174`
- Marketing API on port `3002`

For Hot Leads, Agent 9 should trigger hooks for:

- Marketing Intelligence Module
- Personalized Email Campaign
- Executive Brief Generation
- Slack Notification
- Teams Notification

In the first implementation, these can be safe integration hooks or log-based adapters. They should be easy to replace with real Person 2 API calls.

Use this standard trigger payload for every Person 2 hot-lead integration:

```json
{
  "lead_id": "lead-001",
  "name": "John Smith",
  "company_id": "company-001",
  "company": "ABC Bank",
  "company_domain": "abcbank.example",
  "role": "Security Architect",
  "role_category": "Influencer",
  "industry": "Banking",
  "intent_score": 92,
  "lead_category": "HOT",
  "engaged_categories": ["THREAT", "BREACH"],
  "engaged_category_counts": {
    "THREAT": 4,
    "BREACH": 2
  },
  "recommended_action": "Schedule Security Intelligence Demo",
  "ai_insights": [
    "Engaged with multiple threat intelligence posts",
    "Security influencer likely to shape vendor evaluation",
    "High-value industry",
    "Consistent engagement over time"
  ]
}
```

Recommended Person 2 calls:

```text
POST http://localhost:3002/api/campaigns/generate
POST http://localhost:3002/api/assets/create
POST http://localhost:3002/api/comms/alert
```

Person 2 should be able to generate a personalized email, executive brief, visual asset, Slack alert, and Teams alert from this payload without querying Agent 9 again.

---

## FULL PLATFORM LOOP

Agent 9 completes the SQ1 intelligence-to-revenue loop:

```text
Person 1 Intel Feed
-> Person 2 Marketing Assets
-> LinkedIn Engagement
-> Agent 9 Customer Intelligence
-> Person 2 Campaign Trigger
-> Sales Notification
```

Demo story:

```text
Intel Produced
-> Marketing Published
-> LinkedIn Engagement Captured
-> Lead Scored
-> Campaign Triggered
-> Sales Notified
```

---

## API DESIGN

Create:

```text
openosint/api/routes/customer_intelligence.py
```

Required endpoints:

```text
POST /api/customer-intelligence/analyze
POST /api/customer-intelligence/ingest
GET  /api/customer-intelligence/leads
GET  /api/customer-intelligence/summary
```

Purpose:

- `/analyze` receives a full analysis request.
- `/ingest` receives LinkedIn engagement events directly.
- `/leads` returns dashboard-ready lead data.
- `/summary` returns counts for dashboard stats.

---

## DASHBOARD INTEGRATION

Create:

```text
frontend/src/components/CustomerIntelligenceWidget.jsx
```

This is a widget for the existing SQ1 dashboard, not a new dashboard app.

Widgets:

- Total Leads
- Hot Leads
- Warm Leads
- Companies Identified
- Potential Customers Table
- Lead Insights Panel

Follow Person 1 dashboard style:

- Compact SOC-style cards
- Use Person 1 SOC theme variables:
  - `--bg-card`
  - `--accent-cyan`
  - `--accent-green`
  - `--accent-red`
  - `--accent-orange`
  - `--text-primary`
  - `--text-muted`
  - `--border`
- Inline styles are acceptable because existing components use them
- `lucide-react` icons are available
- Poll API every 30 seconds
- Do not introduce a separate visual language or marketing-style dashboard

---

## MODULE RESPONSIBILITIES

### `openosint/customer_intelligence/models/customer_intelligence.py`

Define Pydantic models:

- `LinkedInEngagement`
- `LeadProfile`
- `CompanyReference`
- `EngagementAnalysis`
- `IntentScoreBreakdown`
- `MarketingTriggerPayload`
- `CustomerLead`
- `CustomerIntelligenceRequest`
- `CustomerIntelligenceResponse`
- `DashboardLeadSummary`

### `openosint/customer_intelligence/services/linkedin_intelligence.py`

Responsibilities:

- Normalize LinkedIn engagement payloads
- Group events by profile
- Classify job titles
- Build lead profiles
- Analyze engagement patterns
- Normalize Person 1 intel categories into engaged topics

### `openosint/customer_intelligence/services/intent_scoring.py`

Responsibilities:

- Calculate engagement score
- Calculate decision power score
- Calculate company fit score
- Return full score breakdown

### `openosint/customer_intelligence/services/lead_classifier.py`

Responsibilities:

- Classify lead category
- Generate recommended action
- Generate AI-style insights from structured signals
- Summarize dashboard counts

### `openosint/customer_intelligence/agent.py`

Responsibilities:

- Orchestrate the full Agent 9 workflow
- Use company intelligence when available
- Score and classify leads
- Trigger hot lead integrations
- Keep Person 2 integrations replaceable

### `openosint/customer_intelligence/integrations/marketing.py`

Responsibilities:

- Build the standard Person 2 hot-lead trigger payload
- Trigger Person 2 email campaign generation
- Trigger Person 2 executive brief or visual asset generation
- Trigger Person 2 Slack and Teams alerts
- Fail safely when Person 2 is offline

### `openosint/data/customer_leads.py`

Responsibilities:

- Persist analyzed leads using Person 1's TinyDB pattern
- Store or update leads by LinkedIn ID/profile URL/name-company key
- Return latest leads for dashboard widgets
- Return summary counts for API routes

Suggested storage:

```text
openosint/data/leads.json
```

or a `customer_leads` table in the existing TinyDB database if that better matches Person 1's current store implementation.

### `openosint/api/routes/customer_intelligence.py`

Responsibilities:

- Provide FastAPI router
- Accept engagement ingestion
- Return lead analysis
- Return dashboard summaries

### `frontend/src/components/CustomerIntelligenceWidget.jsx`

Responsibilities:

- Show Agent 9 metrics inside existing dashboard
- Show potential customers table
- Show selected lead insights
- Show recommended action

---

## DEMO PAYLOAD

Use this kind of payload to test `/ingest`:

```json
[
  {
    "name": "John Smith",
    "company": "ABC Bank",
    "company_domain": "abcbank.example",
    "job_title": "Security Architect",
    "industry": "Banking",
    "seniority": "Senior",
    "linkedin_id": "john-smith-abc",
    "profile_url": "https://www.linkedin.com/in/john-smith-abc",
    "engagement_type": "share",
    "content_category": "Threat Intelligence Posts",
    "intel_topic": "THREAT",
    "content_id": "intel-post-001",
    "content_title": "Ransomware Threat Intelligence Brief",
    "occurred_at": "2026-06-12T08:30:00Z"
  },
  {
    "name": "John Smith",
    "company": "ABC Bank",
    "company_domain": "abcbank.example",
    "job_title": "Security Architect",
    "industry": "Banking",
    "seniority": "Senior",
    "linkedin_id": "john-smith-abc",
    "profile_url": "https://www.linkedin.com/in/john-smith-abc",
    "engagement_type": "comment",
    "content_category": "Breach Reports",
    "intel_topic": "BREACH",
    "content_id": "breach-post-002",
    "content_title": "Banking Sector Breach Report",
    "comment_text": "Useful analysis for banking security teams.",
    "occurred_at": "2026-06-12T09:15:00Z"
  }
]
```

---

## ROADMAP TEMPLATE

Add Agent 9 to the platform roadmap:

```markdown
# SQ1 Security Intelligence Copilot Roadmap

## Agent 9: Customer Intelligence

- [x] LinkedIn-only engagement ingestion model
- [x] Profile discovery
- [x] Company identification
- [x] Person 1 company ID mapping
- [x] Engagement analysis
- [x] Intel topics engaged tracking
- [x] Intent scoring
- [x] Lead classification
- [x] Recommended action generation
- [x] Standard Person 2 hot-lead trigger payload
- [x] Hot lead integration hooks
- [x] Lead persistence
- [x] Dashboard widget

## Next

- [ ] Mount Agent 9 router in the existing FastAPI app
- [ ] Import Customer Intelligence widget into the existing dashboard
- [ ] Replace safe Person 2 hooks with live production API calls
- [ ] Add tests
```

---

## TODO TEMPLATE

Add Agent 9 to TODO:

```markdown
# SQ1 Security Intelligence Copilot TODO

## P0 - Agent 9 Customer Intelligence

- [x] Create customer intelligence models
- [x] Create LinkedIn intelligence service
- [x] Create intent scoring service
- [x] Create lead classifier service
- [x] Create customer intelligence agent
- [x] Create Person 2 integration payload builder
- [x] Create lead persistence helper
- [x] Create FastAPI route file under `openosint/api/routes/`
- [x] Create dashboard widget

## P1 - Integration

- [ ] Mount route in Person 1 FastAPI app
- [ ] Add widget to Person 1 dashboard
- [ ] Confirm company ID/domain/threat score mapping from Person 1 company records
- [ ] Connect Person 2 email campaign trigger
- [ ] Connect Person 2 executive brief trigger
- [ ] Connect Person 2 Slack and Teams alerts
```

---

## RUNBOOK

1. Read `PERSON1_OSINT_MODULE.md`.
2. Read `PERSON2_MARKETING_MODULE.md`.
3. Confirm existing repo structure.
4. Create only the Agent 9 files.
5. Keep API and dashboard code ready to mount/import.
6. Do not modify existing agents unless explicitly asked.
7. Run syntax checks for Python files.
8. Confirm `git status` only shows intended files.

---

## FINAL DEMO STORY

1. SQ1 publishes threat intelligence and breach reports.
2. Person 2 turns that intelligence into LinkedIn-ready marketing assets.
3. LinkedIn users like, comment, share, repost, or follow SQ1 content.
4. Agent 9 groups engagement by person.
5. Agent 9 discovers profile, company, company ID, role, and seniority.
6. Agent 9 tracks the intel topics they engaged with.
7. Agent 9 calculates customer intent score.
8. A Security Architect at ABC Bank becomes a Hot Lead.
9. Agent 9 recommends: `Schedule Security Intelligence Demo`.
10. Hot lead hooks trigger Person 2 marketing/comms actions with the standard payload.
11. Person 1 dashboard shows the lead in the Customer Intelligence widget.

---

## SUCCESS CRITERIA

- Agent 9 uses LinkedIn engagement only.
- Lead scoring matches the requested formula.
- Hot/Warm/Interested/Awareness thresholds are correct.
- Company intelligence is used when available.
- Person 1 company IDs are stored when available.
- Engaged intel topics and counts are returned.
- Leads are persisted through Person 1's data layer.
- Person 2 receives a standard hot-lead payload.
- Hot lead integrations are present and replaceable.
- Widget fits the existing SQ1 dashboard style.
- No separate app, repo, or dashboard is created.
- Person 1 and Person 2 module boundaries remain intact.
