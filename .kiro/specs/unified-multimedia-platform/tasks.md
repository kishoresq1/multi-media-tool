# Implementation Plan: Unified Multimedia Platform

## Overview

This plan migrates and consolidates Zero Day Radar (Python/FastAPI) and OpenOSINT (Node.js/Express marketing module) into a single unified platform. Tasks build the shared foundation first, then the Intelligence_Service backend, then the Content_Service backend, then both React dashboards, and finally the data migration utilities. Property-based tests use Hypothesis (Python) for Intelligence_Service and fast-check (TypeScript) for Content_Service.

## Tasks

- [x] 1. Set up monorepo structure and shared infrastructure
  - Create top-level directories: `intelligence-service/`, `content-service/`, `security-dashboard/`, `marketing-dashboard/`, `migrations/`, `nginx/`
  - Add `docker-compose.yml` defining PostgreSQL :5432, Redis :6379, Ollama :11434, Intelligence_Service :8000, Content_Service :3000, Celery worker, Celery Beat, and Nginx :80 services with environment variable references
  - Add root `.env.example` covering all variables (DB credentials, JWT secret, LLM API keys for Anthropic/OpenAI/OpenRouter/Gemini, LinkedIn OAuth client ID/secret, Slack/Teams webhook URLs, Ollama base URL)
  - Add `nginx/default.conf` routing `/api/v1/intel/*` and `/auth/*` to Intelligence_Service, `/api/v1/content/*` to Content_Service, static assets to respective React bundles
  - _Requirements: 1.1, 1.2, 10.7_

- [ ] 2. Create shared PostgreSQL schema and migrations
  - [-] 2.1 Write Alembic migration scripts for Intelligence_Service tables
    - Define `users`, `unified_intel`, `intel_posts`, `vendor_advisory_intel`, `vulnerability_intel`, `compliance_intel`, `company_breach_intel`, `research_blog_intel`, `job_runs`, `osint_scan_results` with all columns, indexes, and unique constraints (content_hash, cluster_key, CVE deduplication)
    - _Requirements: 1.4, 2.3, 2.6, 3.1, 3.2, 3.3_
  - [ ] 2.2 Write Alembic migration scripts for Content_Service tables
    - Define `content_assets`, `campaigns`, `subscribers`, `linkedin_oauth_tokens`, `approval_queue_history` with all columns, FK constraints, and status enums
    - _Requirements: 7.1, 7.6, 9.1_
  - [ ] 2.3 Add `used_in_marketing` and `used_at` columns to `unified_intel`
    - Add columns and index on `used_in_marketing` for efficient marketing queue queries
    - _Requirements: 1.5, 6.1_

- [ ] 3. Intelligence_Service: authentication and RBAC
  - [ ] 3.1 Implement user registration, login, and JWT issuance endpoints
    - `POST /auth/register` (require role), `POST /auth/login` (return access + refresh tokens), `POST /auth/refresh`, `GET /auth/me`
    - JWT payload: `sub`, `email`, `role`, `iat`, `exp` (access 1 h, refresh 7 d)
    - _Requirements: 10.1, 10.6_
  - [ ] 3.2 Implement role-based dependency guards
    - `require_security_team`, `require_marketing_team`, `require_any_role` FastAPI dependencies
    - Return 403 without revealing resource details on role mismatch; return 401 for missing/invalid token
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6_
  - [ ]* 3.3 Write property test for role-based access denial
    - **Property 8: Role-based access denial**
    - **Validates: Requirements 10.4, 10.5**
    - Generate random `(user_role, endpoint_required_role)` pairs using Hypothesis; assert 403 returned whenever roles differ and no state mutation occurs

- [ ] 4. Intelligence_Service: collector framework and multi-source collection
  - [ ] 4.1 Migrate Zero Day Radar collector modules into `intelligence-service/app/collectors/`
    - Port RSS, HTML scraper, vendor advisory (Microsoft MSRC, Cisco, Fortinet), CVE Program, NVD, exploit DB, social (Reddit, Twitter/Nitter, LinkedIn, HackerNews), and compliance (NIST, ISO, regulatory) collectors
    - Each collector must implement the `BaseCollector` interface: `fetch() -> list[RawSignal]`
    - _Requirements: 2.1, 2.2_
  - [ ] 4.2 Implement deduplication by content hash before storage
    - Compute `content_hash` as SHA-256 of normalized title + content; skip INSERT if hash already exists
    - _Requirements: 2.3, 2.6_
  - [ ]* 4.3 Write unit tests for collector parsing logic
    - Test RSS feed parsing, HTML scraping extraction, and JSON feed parsing with fixture files
    - Test content hash deduplication: inserting the same signal twice results in exactly one row
    - _Requirements: 2.3, 2.6_
  - [ ] 4.4 Implement per-source error isolation
    - Wrap each collector's `fetch()` in try/except; log `source_id` and error, continue to next source; enforce 30-second per-source timeout
    - _Requirements: 2.5_
  - [ ]* 4.5 Write property test for collection cycle fault tolerance
    - **Property 12: Collection cycle fault tolerance**
    - **Validates: Requirements 2.5**
    - Use Hypothesis to generate N-collector setups where a random subset fails; assert remaining collectors complete and pipeline does not abort

- [ ] 5. Intelligence_Service: SAINT scoring and classification engines
  - [ ] 5.1 Implement SAINT threat scoring engine
    - Pure function `score_threat_cluster(cluster: list[RawSignal]) -> ThreatScore`
    - Sum source credibility points from configured mapping; apply additive bonuses (corroboration +10/+15, CVE +10, PoC +15, active exploitation +20); cap at 100
    - _Requirements: 3.1_
  - [ ]* 5.2 Write property test for SAINT threat score bounded output
    - **Property 1: SAINT threat score bounded output**
    - **Validates: Requirements 3.1**
    - Use Hypothesis to generate random clusters (0–20 signals, random boolean flags); assert score ∈ [0, 100] for all inputs
  - [ ] 5.3 Implement SAINT compliance scoring engine
    - Pure function `score_compliance_cluster(cluster: list[ComplianceSignal]) -> ComplianceScore`
    - Sum source credibility points; apply additive bonuses (framework +5, regulatory authority +10/+12, effective date +8, deadline +10); cap at 100
    - _Requirements: 3.2_
  - [ ]* 5.4 Write property test for SAINT compliance score bounded output
    - **Property 2: SAINT compliance score bounded output**
    - **Validates: Requirements 3.2**
    - Use Hypothesis to generate random compliance clusters; assert score ∈ [0, 100] for all inputs
  - [ ] 5.5 Implement risk level assignment from confidence score
    - Map score → LOW (0–20), MEDIUM (21–40), HIGH (41–60), VERY_HIGH (61–80), CRITICAL (81–100)
    - Override to CRITICAL when cluster has ≥3 distinct sources AND active exploitation confirmed
    - _Requirements: 3.4, 3.6_
  - [ ]* 5.6 Write property test for critical risk level threshold
    - **Property 4: Critical risk level threshold**
    - **Validates: Requirements 3.4**
    - Generate clusters with ≥3 distinct sources + active exploitation flag set; assert `risk_level == CRITICAL`
  - [ ] 5.7 Implement SAINT classification engine
    - Keyword pattern matching, source table origin weighting, entity extraction to classify as PRODUCT_VULNERABILITY, COMPANY_BREACH, or UNKNOWN with confidence 0–99
    - Retain UNKNOWN records with confidence < 40 for analyst triage
    - _Requirements: 3.3, 3.7_
  - [ ]* 5.8 Write property test for classification exhaustiveness
    - **Property 3: Classification exhaustiveness**
    - **Validates: Requirements 3.3**
    - Use Hypothesis to generate random unified intel records; assert classification ∈ {PRODUCT_VULNERABILITY, COMPANY_BREACH, UNKNOWN} for all inputs

- [ ] 6. Intelligence_Service: Unified Intel Pipeline (grouping, enrichment, scoring)
  - [ ] 6.1 Implement signal clustering by CVE and vendor/product/version
    - Group signals: CVE identifier match first, then normalized vendor + product + version string
    - `cluster_signals(signals: list[RawSignal]) -> list[Cluster]` pure function
    - _Requirements: 3.5_
  - [ ]* 6.2 Write property test for signal grouping determinism
    - **Property 5: Signal grouping determinism**
    - **Validates: Requirements 3.5**
    - Use Hypothesis to generate random signal lists; shuffle order; assert clustering produces identical cluster assignments regardless of input order
  - [ ] 6.3 Implement Ollama LLM enrichment step
    - Send up to 8 records (≤6000 chars total) per cluster to Ollama; request `vendor_name`, `product_name`, `version_name`, `primary_cve`, `summary`
    - Store results, set `llm_enriched = true`, record `llm_model`
    - Configurable model name, base URL, and timeout (default 120 s)
    - _Requirements: 4.1, 4.3, 4.4_
  - [ ] 6.4 Implement rule-based fallback extraction when Ollama is unavailable
    - Extract vendor/product/version/CVEs from existing source record metadata fields; set `llm_enriched = false`
    - _Requirements: 4.2, 4.5_
  - [ ] 6.5 Implement misinformation detection step
    - Send content + source URL to configured LLM_Provider; receive verdict (LEGITIMATE, MISINFORMATION, UNVERIFIED) and confidence (0.0–1.0)
    - Suppress item from feed and flag for analyst review when verdict == MISINFORMATION and confidence > 0.7
    - _Requirements: 12.6, 12.7_
  - [ ] 6.6 Wire full pipeline: collect → cluster → enrich → score → classify → persist
    - `run_unified_pipeline()` function callable by Celery task and manual trigger endpoint
    - _Requirements: 11.2_

- [ ] 7. Checkpoint — Intelligence_Service core pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Intelligence_Service: background scheduler and job management
  - [ ] 8.1 Configure Celery Beat schedule and task definitions
    - Collection interval configurable via env var, default 20 min, range 5–1440 min
    - Implement per-pipeline Celery tasks: `run_social`, `run_advisories`, `run_blogs`, `run_vulnerabilities`, `run_breaches`, `run_compliance`, `run_unified_pipeline`
    - _Requirements: 11.1, 11.3_
  - [ ] 8.2 Implement retry policy for failed background jobs
    - `max_retries=3`, exponential backoff 60 s → 120 s → 240 s; on final failure write `job_runs.status = failed` with full stack trace
    - _Requirements: 11.6_
  - [ ] 8.3 Implement 45-minute cycle timeout enforcement
    - Celery task time limit of 2700 s; log timeout with last source being processed
    - _Requirements: 2.7_
  - [ ] 8.4 Implement manual run trigger with deduplication guard
    - `POST /api/v1/intel/jobs/{task}/run` — enqueue within 5 s; if same pipeline already running, queue the manual run to execute after it completes
    - Write to `job_runs` table on start and completion
    - _Requirements: 11.5, 11.7_
  - [ ]* 8.5 Write unit tests for job lifecycle
    - Test enqueue → running → completed transition in `job_runs`
    - Test that duplicate concurrent runs are queued, not executed in parallel
    - _Requirements: 11.5, 11.7_

- [ ] 9. Intelligence_Service: intelligence API endpoints
  - [ ] 9.1 Implement unified intel list and detail endpoints
    - `GET /api/v1/intel/unified` — paginated (default 50 items), filterable by classification, vendor, product, min confidence score, date range; ordered by latest_date DESC, confidence_score DESC
    - `GET /api/v1/intel/unified/{id}` — full detail with score_breakdown, source_refs, LLM enrichment data, CVE list, classification reasoning
    - Respond within 5 s for up to 50 items
    - _Requirements: 1.3, 1.8, 5.2, 5.5_
  - [ ] 9.2 Implement domain-specific intel list endpoints
    - `GET /api/v1/intel/advisories`, `/blogs`, `/breaches`, `/compliance`, `/social`, `/vulnerabilities` — up to 500 items per page with pagination
    - _Requirements: 5.3_
  - [ ] 9.3 Implement marketing feed endpoint and `marketing_used` PATCH endpoint
    - `GET /api/v1/intel/feed` — Intel_Items not yet used in marketing, sorted by severity DESC then published_at DESC; fields: id, title, summary, classification, severity, confidence_score, cves, vendor_name, product_name, source_refs, published timestamp
    - `PATCH /api/v1/intel/unified/{id}/used` — set `used_in_marketing=true`, record `used_at`; accessible by marketing_team and service account
    - _Requirements: 1.3, 1.5, 6.1_
  - [ ] 9.4 Implement collector management endpoints
    - `GET /api/v1/intel/collectors` — list collectors with name, description, enabled state, last-run status
    - `PATCH /api/v1/intel/collectors/{id}` — toggle enabled/disabled
    - `GET /api/v1/intel/jobs` — job list with status, last run UTC, next scheduled run
    - _Requirements: 5.4, 5.6, 11.4_
  - [ ]* 9.5 Write unit tests for intelligence API endpoints
    - Test filter combinations, pagination, and empty result responses
    - Test that marketing_team cannot access security-team-only endpoints (403)
    - _Requirements: 5.2, 5.3, 10.4_

- [ ] 10. Intelligence_Service: OSINT investigation tool endpoints
  - [ ] 10.1 Implement company scan endpoint
    - `POST /api/v1/intel/osint/company-scan` — accept domain + optional email; run WHOIS, subdomain enumeration, Google dork generation, breach check with 120 s per-tool timeout
    - Compute threat score 0–100 from discovered exposures; persist to `osint_scan_results`
    - _Requirements: 12.1, 12.4_
  - [ ] 10.2 Implement employee leak detection endpoint
    - `POST /api/v1/intel/osint/employee-leak` — accept email; run HaveIBeenPwned, email footprint enumeration, paste dump search
    - _Requirements: 12.2_
  - [ ] 10.3 Implement infrastructure recon endpoint
    - `POST /api/v1/intel/osint/infra-recon` — accept IP/domain; run Shodan, DNS enumeration, VirusTotal, AbuseIPDB, IP geolocation
    - _Requirements: 12.3_
  - [ ] 10.4 Implement external OSINT source fault isolation
    - Wrap each external tool call; on error include error indicator in response for that tool, return results from remaining tools
    - _Requirements: 12.5_
  - [ ]* 10.5 Write unit tests for OSINT endpoint error isolation
    - Test that individual tool failures return partial results with error indicators rather than a top-level 500
    - _Requirements: 12.5_

- [ ] 11. Checkpoint — Intelligence_Service API complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Content_Service: project setup and JWT validation
  - Set up Node.js/Express project in `content-service/` with TypeScript, Prisma (PostgreSQL), and fast-check for property tests
  - Implement JWT validation middleware using the shared `JWT_SECRET`; extract `role` claim; provide `requireMarketingTeam` middleware
  - _Requirements: 10.3, 10.6_

- [ ] 13. Content_Service: AI provider selection and fallback templates
  - [ ] 13.1 Implement LLM provider selection logic
    - Check API keys in priority order: Anthropic → OpenRouter → OpenAI → Gemini; use first key present
    - Abstract provider behind `LLMProvider` interface: `generate(prompt: string): Promise<string>`
    - _Requirements: 8.4_
  - [ ] 13.2 Implement deterministic fallback templates for all content types
    - Fallback templates for email campaign, HyperFrame visual spec, Remotion video spec, LinkedIn post, Slack Block Kit message, Teams message card
    - All fallback outputs must satisfy the same field constraints as AI-generated content (no null or empty required fields)
    - _Requirements: 8.5_
  - [ ]* 13.3 Write property test for LLM fallback determinism
    - **Property 10: LLM fallback determinism**
    - **Validates: Requirements 8.5**
    - Use fast-check to generate random Intel_Items with LLM provider set to unavailable; assert all required fields present and non-empty in fallback output for all content types

- [ ] 14. Content_Service: approval queue and content asset state machine
  - [ ] 14.1 Implement content_asset creation with PENDING_REVIEW status
    - Every content generation handler must create a `content_assets` row with `status = pending_review`, `created_at`, and generating user ID before returning the response
    - _Requirements: 7.1_
  - [ ] 14.2 Implement approval queue endpoints
    - `GET /api/v1/content/approval-queue` — list assets sorted by created_at DESC with status badges
    - `GET /api/v1/content/approval-queue/{id}` — detail + preview
    - `POST /api/v1/content/approval-queue/{id}/approve` — set status APPROVED, record reviewer ID and timestamp
    - `POST /api/v1/content/approval-queue/{id}/reject` — set status REJECTED, store reviewer notes (max 2000 chars)
    - `PATCH /api/v1/content/approval-queue/{id}/edit` — store both original AI content and edited content with edit timestamp
    - _Requirements: 7.2, 7.3, 7.4, 7.6_
  - [ ] 14.3 Implement re-submission of rejected assets
    - When a reviewer re-submits a REJECTED asset after editing, set status back to PENDING_REVIEW and insert a new `approval_queue_history` entry
    - _Requirements: 7.7_
  - [ ] 14.4 Enforce approval gate on publish/distribute actions
    - Any publish or distribute handler must reject with 400 if `content_assets.status != approved`
    - _Requirements: 7.5_
  - [ ]* 14.5 Write property test for content asset state machine validity
    - **Property 9: Content asset state machine validity**
    - **Validates: Requirements 7.3, 7.4**
    - Use fast-check to generate random transition sequences; assert only PENDING_REVIEW→APPROVED, PENDING_REVIEW→REJECTED, APPROVED→PUBLISHED succeed; all other transitions return 409
  - [ ]* 14.6 Write property test for content generation always produces approval queue entry
    - **Property 6: Content generation always produces approval queue entry**
    - **Validates: Requirements 7.1**
    - Use fast-check to generate random valid Intel_Items and content type combinations; assert exactly one `content_assets` row with PENDING_REVIEW status is created for each generation request
  - [ ]* 14.7 Write property test for approval edit preserves original
    - **Property 13: Approval edit preserves original**
    - **Validates: Requirements 7.6**
    - Use fast-check to generate random content assets and edits; assert `ai_generated_content` field is unchanged after PATCH edit while `human_edited_content` reflects the edit

- [ ] 15. Content_Service: AI-assisted content generation endpoints
  - [ ] 15.1 Implement email campaign generation endpoint
    - `POST /api/v1/content/campaigns/generate` — validate Intel_Item has id + title; generate campaign with all required fields (subject ≤160, preheader ≤180, headline ≤160, body HTML, CTA ≤60, recommended action ≤220, tone, template type); create content_asset + approval queue entry
    - _Requirements: 8.1, 8.6_
  - [ ] 15.2 Implement HyperFrame visual specification generation endpoint
    - `POST /api/v1/content/hyperframe/generate` — generate visual spec with all required fields (headline ≤80, subheadline ≤120, body ≤240, severity ≤60, CVE badge or null, 1–5 hashtags each ≤24, CTA ≤40, color scheme enum, stat highlight ≤60 or null)
    - `POST /api/v1/content/hyperframe/{id}/render` — render PNG 1200×628px from spec; store file path on content_asset
    - _Requirements: 6.3, 8.2_
  - [ ] 15.3 Implement Remotion video composition generation endpoint
    - `POST /api/v1/content/video/generate` — generate video spec (title ≤120, duration 30/45/60s, scene breakdown 3/4/5 scenes with scene number, duration, on-screen text ≤80, narration ≤220, visual direction ≤180, background style ≤40, closing CTA ≤60)
    - `POST /api/v1/content/video/{id}/render` — trigger Remotion render and produce MP4; store file path
    - _Requirements: 6.4, 8.3_
  - [ ] 15.4 Implement Slack Block Kit alert message generation endpoint
    - `POST /api/v1/content/comms/slack` — generate Block Kit message containing Intel_Item title, confidence score, risk level, vendor/product, primary CVE, summary ≤280 chars; create content_asset entry
    - _Requirements: 13.2_
  - [ ] 15.5 Implement Microsoft Teams message card generation endpoint
    - `POST /api/v1/content/comms/teams` — generate Teams Adaptive Card with same fields as Slack message; create content_asset entry
    - _Requirements: 13.3_
  - [ ]* 15.6 Write unit tests for content field constraint validation
    - Test that generated fields respect all character limits and enum constraints for email, HyperFrame, video, and alert types
    - Test that missing Intel_Item `id` or `title` returns 400 with field names
    - _Requirements: 8.1, 8.2, 8.3, 8.6_

- [ ] 16. Content_Service: LinkedIn OAuth and posting
  - [ ] 16.1 Implement LinkedIn OAuth 2.0 flow
    - `GET /auth/linkedin/login` — redirect to LinkedIn authorization URL with OpenID Connect and member social posting scopes
    - `GET /auth/linkedin/callback` — exchange code for tokens; store access token, refresh token, `expires_at`, member URN, and display name in `linkedin_oauth_tokens`
    - `POST /api/v1/content/linkedin/disconnect` — delete stored tokens
    - _Requirements: 9.1_
  - [ ] 16.2 Implement LinkedIn post preview and publish endpoints
    - `GET /api/v1/content/linkedin/status` — return connection status, display name, posting mode
    - `GET /api/v1/content/linkedin/preview/{intel_id}` — generate preview with commentary ≤3000 chars, character count, optional image/video card
    - `POST /api/v1/content/linkedin/post` — enforce `human_verified == true`; publish via LinkedIn Share API within 120 s; handle duplicate post error and non-success API responses; return error with API status code on failure
    - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.8_
  - [ ] 16.3 Implement LinkedIn token expiry guard
    - Middleware checks token `expires_at` before any post operation; if expired or missing, return 401 with re-auth URL
    - _Requirements: 9.7_
  - [ ]* 16.4 Write property test for human verification gate for LinkedIn publishing
    - **Property 7: Human verification gate for LinkedIn publishing**
    - **Validates: Requirements 7.5, 9.3**
    - Use fast-check to generate random post requests where `human_verified` is false or absent; assert all return error and no LinkedIn API call is made
  - [ ]* 16.5 Write unit tests for LinkedIn OAuth and error handling
    - Test expired token returns 401 with login URL
    - Test duplicate post error returns correct error message
    - Test non-existent Intel_Item returns 404
    - _Requirements: 9.4, 9.5, 9.7, 9.8_

- [ ] 17. Content_Service: subscriber management and asset gallery endpoints
  - Implement `GET/POST /api/v1/content/subscribers`, `DELETE /api/v1/content/subscribers/{id}` — subscriber CRUD with email (unique), name, company, active flag, preference fields
  - Implement `GET /api/v1/content/assets` — gallery with filter by asset_type (email, hyperframe, video, linkedin_post, slack_msg, teams_msg); `GET /api/v1/content/assets/{id}/download` — return file
  - Implement `GET /api/v1/content/campaigns` and `POST /api/v1/content/campaigns/{id}/send` — send only APPROVED campaigns; record delivery status
  - _Requirements: 6.2, 6.7, 6.8, 6.9_

- [ ] 18. Content_Service: inter-service `marketing_used` sync with retry
  - After successful content creation, call `PATCH /api/v1/intel/unified/{id}/used` using a service-account JWT
  - On failure, retry up to 3 times with exponential backoff; log failure if all retries exhausted
  - If Intelligence_Service is unreachable at content generation time, return error — do not generate content from missing intel
  - _Requirements: 1.5, 1.6, 1.7_

- [ ] 19. Checkpoint — Content_Service complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Security Dashboard: project setup and API client
  - Initialize React/TypeScript project in `security-dashboard/` with Vite, TailwindCSS, React Query, and React Router
  - Implement API client module pointing to `/api/v1/intel` (behind Nginx); include JWT attach interceptor and 401 redirect to login
  - Implement login page consuming `POST /auth/login`; store tokens in memory (access) and HttpOnly cookie (refresh)
  - _Requirements: 5.7, 10.6_

- [ ] 21. Security Dashboard: live intelligence feed view
  - [ ] 21.1 Implement intelligence feed component
    - Poll `GET /api/v1/intel/unified` every ≤30 s; display items sorted by latest_date DESC, confidence_score DESC
    - Color-code rows by risk level: Critical (score 70–100) red, High (40–69) orange, Medium (20–39) yellow, Low (0–19) grey
    - Show empty state message with "adjust filters or trigger a collection run" when no results match filters
    - _Requirements: 5.1, 5.8_
  - [ ] 21.2 Implement filter controls
    - Filter inputs for classification (PRODUCT_VULNERABILITY, COMPANY_BREACH, UNKNOWN), vendor name, product name, minimum confidence score slider (0–100), date range pickers (start/end)
    - _Requirements: 5.2_
  - [ ] 21.3 Implement drill-down panel for Intel_Item detail
    - Show SAINT score breakdown, source references with links, LLM enrichment data, CVE list, and classification reasoning
    - _Requirements: 5.5_
  - [ ] 21.4 Implement domain-specific views with pagination
    - Tabs or nav for Advisories, Research Blogs, Breaches, Compliance, Social Intelligence, Vulnerabilities — each showing up to 500 items per page
    - _Requirements: 5.3_

- [ ] 22. Security Dashboard: source management and jobs views
  - [ ] 22.1 Implement source management interface
    - `GET /api/v1/intel/collectors` to list collectors with name, description, enabled state, last-run status; toggle switch calls `PATCH /api/v1/intel/collectors/{id}`
    - _Requirements: 5.4_
  - [ ] 22.2 Implement jobs management view
    - `GET /api/v1/intel/jobs` polled every ≤30 s; display task name, status badge (running/completed/failed), last execution UTC, next scheduled run, and "Run Now" button
    - "Run Now" calls `POST /api/v1/intel/jobs/{task}/run`
    - _Requirements: 5.6, 11.4, 11.5_
  - [ ] 22.3 Implement API connection error banner
    - If any fetch to Intelligence_Service fails with network error, display banner with message and configured backend URL
    - _Requirements: 5.7_

- [ ] 23. Marketing Dashboard: project setup and intel queue view
  - Initialize React/TypeScript project in `marketing-dashboard/` with same stack as Security Dashboard; point API client to both `/api/v1/intel` (read-only) and `/api/v1/content`
  - Implement intel queue view consuming `GET /api/v1/intel/feed`; sort by severity DESC then published_at DESC; show items not yet used in marketing
  - _Requirements: 6.1, 10.3_

- [ ] 24. Marketing Dashboard: content generation interfaces
  - [ ] 24.1 Implement campaign builder UI
    - Select Intel_Items from queue; call `POST /api/v1/content/campaigns/generate`; show generated draft in preview panel
    - _Requirements: 6.2_
  - [ ] 24.2 Implement HyperFrame Studio UI
    - Visual spec form with color scheme selector (6 options); call `POST /api/v1/content/hyperframe/generate` then `POST /api/v1/content/hyperframe/{id}/render`; show PNG preview
    - _Requirements: 6.3_
  - [ ] 24.3 Implement video composer UI
    - Duration selector (30/45/60 s); in-browser preview using Remotion Player; call generate then render endpoints
    - _Requirements: 6.4_
  - [ ] 24.4 Implement LinkedIn posting interface
    - Commentary editor (max 3000 chars) with live character count; image/video card attachment selector; call preview endpoint; confirmation submits with `human_verified: true`
    - Display connection status, authenticated display name, and posting mode from `GET /api/v1/content/linkedin/status`
    - _Requirements: 6.5, 9.2, 9.3, 9.6_
  - [ ] 24.5 Implement communications panel (Slack/Teams)
    - Form to compose Slack Block Kit and Teams Adaptive Card messages from Intel_Items; delivery status indicators after send
    - _Requirements: 6.6_

- [ ] 25. Marketing Dashboard: approval queue, asset gallery, and subscriber management
  - Implement approval queue view: list pending/approved/rejected assets sorted by created_at DESC; preview panel; approve/reject/edit actions
  - Implement asset gallery: filter by asset_type; download button; reuse button pre-populates the relevant builder
  - Implement subscriber management: add/remove/list subscribers with preference fields (threat types, min severity, industry)
  - _Requirements: 6.7, 6.8, 6.9, 7.2_

- [ ] 26. Checkpoint — Both dashboards complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 27. Data migration utilities
  - [ ] 27.1 Implement Zero Day Radar SQLite migration utility
    - Script `migrations/migrate_zero_day_radar.py` reads SQLite tables (advisories, blogs, breaches, compliance, social intel, unified intel, vulnerabilities) and inserts into PostgreSQL, preserving `created_at`, `updated_at`, original IDs, CVE IDs, and source attribution
    - _Requirements: 14.3, 14.4_
  - [ ] 27.2 Implement OpenOSINT TinyDB migration utility
    - Script `migrations/migrate_openosint_intel.py` reads TinyDB JSON records and inserts into PostgreSQL `intel_posts` and related tables
    - _Requirements: 14.1, 14.4_
  - [ ] 27.3 Implement OpenOSINT Lowdb marketing data migration utility
    - Script `migrations/migrate_openosint_marketing.py` reads Lowdb JSON (campaigns, subscribers, assets) and inserts into `campaigns`, `subscribers`, `content_assets`
    - _Requirements: 14.2, 14.4_
  - [ ] 27.4 Implement duplicate merge logic
    - When duplicate encountered (matching CVE ID, title hash, or source URL), retain metadata from record with most recent `updated_at`; append distinct source references not already present
    - _Requirements: 14.5_
  - [ ] 27.5 Implement migration summary report output
    - Each migration script prints: total records read, successfully imported, skipped (duplicates), failed, and elapsed time
    - On missing required fields or schema mismatch, log record identifier + failure reason and continue
    - _Requirements: 14.6, 14.7_
  - [ ] 27.6 Implement idempotent re-run guard
    - Track migrated records in a `migration_log` table keyed by (source_origin, original_record_id); skip records already present
    - _Requirements: 14.8_
  - [ ]* 27.7 Write property test for migration timestamp preservation
    - **Property 14: Migration timestamp preservation**
    - **Validates: Requirements 14.4**
    - Use Hypothesis to generate random source records with varying timestamps and source attribution; run migration; assert `created_at` and source attribution fields are identical in destination
  - [ ]* 27.8 Write property test for CVE deduplication idempotence
    - **Property 11: CVE deduplication idempotence**
    - **Validates: Requirements 2.6**
    - Use Hypothesis to generate random CVE entry lists with duplicates; run storage function multiple times; assert exactly one row per unique CVE identifier in `vulnerability_intel`

- [ ] 28. Final checkpoint — Full system integration
  - Ensure all tests pass across Intelligence_Service, Content_Service, both dashboards, and migration utilities
  - Verify Docker Compose stack starts cleanly with `docker-compose up`
  - Ask the user if any questions arise before handing off.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python/Intelligence_Service) and fast-check (TypeScript/Content_Service), minimum 100 iterations each
- Each property test must include a comment tag: `Feature: unified-multimedia-platform, Property {N}: {title}`
- Unit tests focus on specific examples, edge cases, and error conditions
- Checkpoints ensure incremental validation at meaningful integration boundaries

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"] },
    { "wave": 2, "tasks": ["3", "4"] },
    { "wave": 3, "tasks": ["5", "6", "7"] },
    { "wave": 4, "tasks": ["8", "9", "10", "11"] },
    { "wave": 5, "tasks": ["12", "13", "14", "15", "16", "17", "18", "19"] },
    { "wave": 6, "tasks": ["20", "21", "22", "23", "24", "25", "26"] },
    { "wave": 7, "tasks": ["27", "28"] }
  ]
}
```
