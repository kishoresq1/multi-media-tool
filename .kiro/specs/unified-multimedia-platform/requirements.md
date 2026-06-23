# Requirements Document

## Introduction

The Unified Multimedia Platform consolidates two existing projects — OpenOSINT (a cybersecurity intelligence platform with marketing automation) and Zero Day Radar (a cyber threat intelligence hunter) — into a single cohesive multi-media intelligence tool. The platform serves two distinct teams through role-separated dashboards: a Security Team Dashboard for threat intelligence, vulnerability tracking, and compliance monitoring; and a Marketing Team Dashboard for AI-assisted content generation, campaign management, and social media publishing. All automated content generation requires human-in-the-loop approval before publishing or distribution.

## Glossary

- **Platform**: The unified multi-media intelligence system combining OpenOSINT and Zero Day Radar capabilities
- **Intelligence_Service**: The Python/FastAPI backend handling threat intelligence collection, scoring, enrichment, and storage
- **Content_Service**: The Node.js/Express backend handling AI-assisted content generation, campaign management, and subscriber operations
- **Security_Dashboard**: The React frontend serving the security team with threat intel feeds, vulnerability tracking, compliance monitoring, and source management
- **Marketing_Dashboard**: The React frontend serving the marketing team with content generation, campaign building, social media posting, and asset management
- **Collector**: An automated module that fetches intelligence from external sources (RSS, social media, vendor advisories, vulnerability databases, compliance feeds)
- **SAINT_Engine**: The Scoring, Analysis, and Intelligence Normalization for Threats engine that calculates confidence scores (0-100) for intelligence clusters
- **Unified_Intel_Pipeline**: The processing pipeline that collects signals from all sources, groups them by vendor/product/CVE, enriches via LLM, scores with SAINT, and classifies threats
- **Approval_Queue**: A staging area where AI-generated content awaits human review and explicit approval before publishing
- **Content_Asset**: Any generated marketing artifact including emails, HyperFrame visuals, Remotion videos, LinkedIn posts, and Slack/Teams messages
- **Background_Scheduler**: The Celery+Redis task execution system that runs collection jobs on configurable intervals
- **LLM_Provider**: An AI language model service used for enrichment and content generation, supporting Anthropic Claude, OpenAI, OpenRouter, Gemini, and Ollama (local)
- **Intel_Item**: A normalized intelligence record with classification, severity, scoring, and source attribution
- **Role**: A user's team assignment (security_team or marketing_team) that determines dashboard access and available operations

## Requirements

### Requirement 1: Unified API Gateway

**User Story:** As a platform operator, I want both dashboards to communicate through a single API layer, so that intelligence data flows seamlessly between security collection and marketing content generation without duplicate data stores.

#### Acceptance Criteria

1. THE Intelligence_Service SHALL expose all threat intelligence endpoints (collection, scoring, enrichment, unified intel, vulnerabilities, advisories, breaches, compliance, social intel) under the `/api/v1` versioned prefix
2. THE Content_Service SHALL expose all content generation endpoints (email campaigns, HyperFrame visuals, Remotion videos, LinkedIn posts, Slack/Teams alerts, subscriber management) under the `/api/v1` versioned prefix
3. WHEN the Marketing_Dashboard requests intelligence data for content generation, THE Intelligence_Service SHALL return Intel_Items containing at minimum: item identifier, title, summary, classification, severity, SAINT confidence score, CVE identifiers, vendor name, product name, source references, and published timestamp, and THE Content_Service SHALL accept these fields as input for content generation without transformation
4. THE Platform SHALL use a shared PostgreSQL database for intelligence data accessible by both services
5. WHEN the Content_Service generates content from an Intel_Item and receives a successful content creation response, THE Content_Service SHALL send a PATCH request to the Intelligence_Service to set the Intel_Item's `marketing_used` flag to true and record the generated Content_Asset identifier
6. IF the Intelligence_Service is unreachable when the Content_Service requests intel data, THEN THE Content_Service SHALL return an error indicating the intelligence source is temporarily unavailable and SHALL NOT generate content from stale or missing data
7. IF the Content_Service fails to mark an Intel_Item as used in marketing due to a network or service error, THEN THE Content_Service SHALL retry the request up to 3 times with exponential backoff and log the failure if all retries are exhausted
8. WHEN the Marketing_Dashboard requests intelligence data for content generation, THE Intelligence_Service SHALL respond within 5 seconds for result sets of up to 50 Intel_Items

### Requirement 2: Multi-Source Intelligence Collection

**User Story:** As a security analyst, I want the platform to automatically collect threat intelligence from all configured sources, so that I have comprehensive visibility into the threat landscape without manual monitoring.

#### Acceptance Criteria

1. THE Collector SHALL support fetching from RSS feeds, HTML-scraped research blogs, vendor advisories (Microsoft MSRC, Cisco, Fortinet), CVE Program, NVD, exploit databases, and social sources (Reddit, Twitter/Nitter, LinkedIn, HackerNews)
2. THE Collector SHALL support fetching from compliance sources (NIST frameworks, ISO updates, regulatory feeds)
3. WHEN a collection cycle completes, THE Intelligence_Service SHALL store each signal whose content hash does not already exist in the database, recording source_id, source_name, collection_method, published_at timestamp, and raw content for each stored entry
4. THE Background_Scheduler SHALL execute collection jobs at a configurable interval between 5 and 1440 minutes, with a default of 20 minutes
5. IF a Collector source is unreachable or returns an error within the per-source request timeout of 30 seconds, THEN THE Intelligence_Service SHALL log the failure including source_id and error description, skip that source, and continue collecting from remaining sources without interrupting the cycle
6. WHEN the Intelligence_Service polls NVD and CISA Known Exploited Vulnerabilities feeds, THE Intelligence_Service SHALL deduplicate entries by CVE identifier before storage
7. IF a collection cycle exceeds 45 minutes of total elapsed time, THEN THE Background_Scheduler SHALL terminate the cycle and log a timeout failure indicating the last source being processed

### Requirement 3: SAINT Threat Scoring and Classification

**User Story:** As a security analyst, I want collected intelligence to be automatically scored and classified, so that I can prioritize the most critical threats without manually triaging every signal.

#### Acceptance Criteria

1. WHEN the Unified_Intel_Pipeline processes collected threat-domain signals, THE SAINT_Engine SHALL calculate a threat confidence score from 0 to 100 by summing source credibility points (assigned per source based on a configured source-score mapping) and applying additive bonuses for corroboration count (2 sources: +10, 3+ sources: +15), CVE presence (+10), proof-of-concept availability (+15), and active exploitation status (+20), capping the total at 100
2. WHEN the Unified_Intel_Pipeline processes compliance-domain signals, THE SAINT_Engine SHALL calculate a separate compliance score from 0 to 100 by summing source credibility points (assigned per source based on a configured compliance source-score mapping) and applying additive bonuses for framework identification (+5), regulatory source authority indicated by framework update (+10) or new requirement (+12), and update significance indicated by effective date (+8) or deadline presence (+10), capping the total at 100
3. THE SAINT_Engine SHALL classify each unified intel record as PRODUCT_VULNERABILITY, COMPANY_BREACH, or UNKNOWN based on keyword pattern matching against content, source table origin weighting, and entity extraction of vendor/product/company names, and SHALL assign a classification confidence value from 0 to 99
4. WHEN a cluster has signals from three or more sources with distinct source identifiers and active exploitation is confirmed by at least one authoritative exploitation catalog entry, THE SAINT_Engine SHALL assign a risk level of CRITICAL
5. THE Unified_Intel_Pipeline SHALL group related signals into clusters by matching CVE identifiers first, then by normalized vendor name, product name, and version string, before passing each cluster to scoring
6. WHEN the SAINT_Engine produces a threat confidence score for a cluster, THE SAINT_Engine SHALL assign a risk level of LOW (0–20), MEDIUM (21–40), HIGH (41–60), VERY_HIGH (61–80), or CRITICAL (81–100) based on the final confidence score
7. IF a unified intel record receives a classification of UNKNOWN with a classification confidence below 40, THEN THE SAINT_Engine SHALL retain the record with the UNKNOWN classification and the computed score so that an analyst can manually triage it

### Requirement 4: LLM-Powered Intelligence Enrichment

**User Story:** As a security analyst, I want collected signals to be enriched with structured metadata extracted by AI, so that I can search and filter intelligence by vendor, product, and version without relying on inconsistent source formatting.

#### Acceptance Criteria

1. WHEN the Unified_Intel_Pipeline processes a signal cluster, THE Intelligence_Service SHALL send up to 8 records (truncated to 6000 characters total) of cluster context to the configured LLM_Provider for entity extraction, requesting a structured response containing vendor_name, product_name, version_name, primary_cve, and summary fields
2. IF the configured LLM_Provider (Ollama) is unavailable or returns a non-200 response, THEN THE Intelligence_Service SHALL proceed with rule-based extraction using existing metadata fields (vendor, product, version, CVEs) from the source records and skip LLM enrichment without failing the pipeline
3. THE Intelligence_Service SHALL support Ollama as the local LLM_Provider for enrichment with configurable model name, base URL, and timeout (default 120 seconds)
4. WHEN LLM enrichment completes successfully, THE Intelligence_Service SHALL store the extracted vendor_name, product_name, version_name, primary_cve, and summary in the unified intelligence record, populate the llm_model field with the model used, and set the llm_enriched flag to true
5. IF the LLM_Provider returns a response that cannot be parsed as valid JSON or returns null for both vendor_name and product_name, THEN THE Intelligence_Service SHALL fall back to the rule-based extracted values from source record metadata and set the llm_enriched flag to false

### Requirement 5: Security Team Dashboard

**User Story:** As a security analyst, I want a dedicated dashboard showing real-time threat intelligence with scoring, filtering, and drill-down capabilities, so that I can monitor the threat landscape and respond to critical issues.

#### Acceptance Criteria

1. THE Security_Dashboard SHALL display a live intelligence feed that auto-refreshes at a maximum interval of 30 seconds, sorted by latest date descending as primary sort and confidence score descending as secondary sort, with items color-coded by risk level: Critical (score 70–100), High (score 40–69), Medium (score 20–39), and Low (score 0–19)
2. THE Security_Dashboard SHALL provide filtering by classification (PRODUCT_VULNERABILITY, COMPANY_BREACH, UNKNOWN), vendor name, product name, minimum confidence score (0–100), and date range (start date and end date)
3. THE Security_Dashboard SHALL display dedicated views for Advisories, Research Blogs, Breaches, Compliance updates, Social Intelligence, and Vulnerabilities, each showing up to 500 items per page with pagination controls
4. THE Security_Dashboard SHALL display a source management interface where analysts can view configured collectors with their name, description, current enabled state, and last-run status (running, completed, failed, or never_run), and toggle individual sources between enabled and disabled states
5. WHEN a security analyst selects an Intel_Item, THE Security_Dashboard SHALL display the full detail in a drill-down panel including SAINT score breakdown (source credibility score, corroboration count, CVE presence, proof-of-concept availability, active exploitation status), source references with links, LLM enrichment data (vendor_name, product_name, version_name, summary), CVE list, and classification reasoning
6. THE Security_Dashboard SHALL display a jobs management view showing each background collection task with its current status (running, completed, failed), last execution timestamp in UTC, and a button to trigger a manual collection run for that specific pipeline
7. IF the Intelligence_Service is unreachable when the Security_Dashboard attempts to load data, THEN THE Security_Dashboard SHALL display an error message indicating the API connection failure and the configured backend URL
8. IF the live intelligence feed contains no items matching the current filter criteria, THEN THE Security_Dashboard SHALL display an empty state message indicating no results were found and suggesting the analyst adjust filters or trigger a collection run

### Requirement 6: Marketing Team Dashboard

**User Story:** As a marketing team member, I want a dedicated dashboard for creating and managing security-focused marketing content, so that I can produce campaigns, visuals, and social posts from vetted intelligence without needing direct access to the security tools.

#### Acceptance Criteria

1. THE Marketing_Dashboard SHALL display an intel queue showing Intel_Items that have not yet been used in marketing, sorted by severity descending (CRITICAL, HIGH, MEDIUM, LOW, INFO) as primary sort and published timestamp descending as secondary sort
2. THE Marketing_Dashboard SHALL provide a campaign builder interface where marketers can select Intel_Items and generate email campaigns using AI assistance
3. THE Marketing_Dashboard SHALL provide a HyperFrame Studio for generating visual content cards (PNG, 1200×628px) from Intel_Items with 6 configurable color schemes (threat_red, compliance_blue, vuln_amber, breach_dark, misinfo_green, digest_purple)
4. THE Marketing_Dashboard SHALL provide a video composer using Remotion for generating video content (30s, 45s, or 60s) from Intel_Items with in-browser preview playback
5. THE Marketing_Dashboard SHALL provide a LinkedIn posting interface with post preview, image/video card attachment, commentary editing (max 3000 characters), and character count display
6. THE Marketing_Dashboard SHALL provide a communications panel for composing Slack Block Kit and Microsoft Teams message cards from Intel_Items with delivery status indicators
7. THE Marketing_Dashboard SHALL provide an asset gallery displaying all previously generated Content_Assets with filtering by asset type (email, visual, video, social post, alert), download capability, and reuse action that pre-populates the relevant content builder
8. THE Marketing_Dashboard SHALL provide a subscriber management interface for adding, removing, and listing email subscribers with preference fields (threat types, minimum severity, industry)
9. THE Marketing_Dashboard SHALL display the Approval_Queue showing pending, approved, and rejected Content_Assets with their current status badges

### Requirement 7: Human-in-the-Loop Content Approval

**User Story:** As a team lead, I want all AI-generated content to require explicit human approval before publishing or distribution, so that the organization maintains quality control and avoids distributing incorrect or inappropriate communications.

#### Acceptance Criteria

1. WHEN the Content_Service generates a Content_Asset (email, visual, video, social post, or alert message), THE Content_Service SHALL place the asset in the Approval_Queue with status PENDING_REVIEW and record the creation timestamp and generating user identifier
2. THE Marketing_Dashboard SHALL display the Approval_Queue sorted by creation date (most recent first) with preview capabilities showing the rendered content for each pending Content_Asset
3. WHEN a human reviewer approves a Content_Asset, THE Content_Service SHALL update the asset status to APPROVED, record the reviewer identifier and approval timestamp, and enable the publish action for that asset only
4. WHEN a human reviewer rejects a Content_Asset, THE Content_Service SHALL update the asset status to REJECTED, store reviewer notes (maximum 2000 characters) explaining the rejection reason, and retain the asset for reference
5. IF a publish or distribute request is made for a Content_Asset whose status is not APPROVED, THEN THE Content_Service SHALL reject the request with an error indicating human approval is required
6. WHEN a human reviewer edits a Content_Asset before approval, THE Content_Service SHALL store both the original AI-generated version and the human-edited version with the edit timestamp
7. WHEN a human reviewer re-submits a previously REJECTED Content_Asset after editing, THE Content_Service SHALL update the asset status to PENDING_REVIEW and place it back in the Approval_Queue as a new review cycle

### Requirement 8: AI-Assisted Content Generation

**User Story:** As a marketing team member, I want AI to generate draft content from intelligence items, so that I can produce professional campaigns faster while still controlling the final output.

#### Acceptance Criteria

1. WHEN a marketer requests email generation from an Intel_Item, THE Content_Service SHALL produce an email campaign where every field is present and non-empty: subject (max 160 characters), preheader (max 180 characters), headline (max 160 characters), body (HTML-safe markup), call-to-action text (max 60 characters), recommended action (max 220 characters), tone classification (one of: urgent, informative, corrective, digest), and template type (one of: breach, compliance, misinfo, vuln, threat)
2. WHEN a marketer requests a HyperFrame visual from an Intel_Item, THE Content_Service SHALL produce a visual content specification where every field is present and non-empty: headline (max 80 characters), subheadline (max 120 characters), body text (max 240 characters), severity label (max 60 characters), CVE badge (valid CVE identifier or null), hashtags (1 to 5 items, each max 24 characters), call-to-action (max 40 characters), color scheme (one of: threat_red, vuln_amber, breach_dark, compliance_blue, misinfo_green, digest_purple), and stat highlight (max 60 characters or null)
3. WHEN a marketer requests a video from an Intel_Item, THE Content_Service SHALL produce a Remotion video composition containing: a title (max 120 characters), a duration (one of: 30, 45, or 60 seconds), a scene breakdown (3 scenes for 30s, 4 for 45s, 5 for 60s) where each scene includes scene number, duration in seconds, on-screen text (max 80 characters), narration text (max 220 characters), visual direction note (max 180 characters), and background style identifier (max 40 characters), and a closing call-to-action (max 60 characters)
4. THE Content_Service SHALL support multiple LLM_Providers (Anthropic Claude, OpenAI, OpenRouter, Gemini) for content generation and SHALL select the active provider by checking configured API keys in priority order: Anthropic first, then OpenRouter, then OpenAI, then Gemini, using the first provider whose API key is present
5. IF the configured LLM_Provider is unavailable (API key not set, or the API call returns an error), THEN THE Content_Service SHALL generate content using deterministic fallback templates that produce valid output conforming to the same field structure and constraints as AI-generated content, without AI assistance
6. IF a content generation request provides an Intel_Item missing the required fields (id and title), THEN THE Content_Service SHALL reject the request with an error indicating the missing fields

### Requirement 9: Social Media Publishing (LinkedIn)

**User Story:** As a marketing team member, I want to publish approved intelligence posts to LinkedIn with attached media, so that the organization can share threat awareness content with its professional network.

#### Acceptance Criteria

1. THE Platform SHALL support LinkedIn OAuth 2.0 authentication for personal profile posting with scopes for OpenID Connect and member social posting
2. WHEN a marketer requests a LinkedIn post, THE Content_Service SHALL generate a post preview containing commentary text (maximum 3000 characters), character count, and optionally an image card (PNG) or video card (MP4) rendered from the Intel_Item
3. WHEN a marketer confirms a LinkedIn post with human_verified set to true, THE Content_Service SHALL publish the post to the authenticated LinkedIn profile using the LinkedIn Share API within 120 seconds
4. IF the LinkedIn Share API returns a non-success response, THEN THE Content_Service SHALL return an error indicating the failure reason including the API status code without publishing the post
5. IF the LinkedIn Share API returns a duplicate post error, THEN THE Content_Service SHALL return an error indicating the content was already posted and the user must edit the text or wait before posting again
6. THE Marketing_Dashboard SHALL display LinkedIn connection status (connected or disconnected), authenticated display name, and posting mode (member or organization)
7. IF the LinkedIn OAuth token is expired or missing, THEN THE Content_Service SHALL reject post operations with an error indicating re-authentication is required and provide the login URL for the user to re-authenticate
8. IF the referenced Intel_Item does not exist, THEN THE Content_Service SHALL return an error indicating the record was not found

### Requirement 10: Role-Based Access Control

**User Story:** As a platform administrator, I want users to access only their team's dashboard and relevant API endpoints, so that security analysts do not accidentally modify marketing content and marketers cannot alter intelligence collection settings.

#### Acceptance Criteria

1. WHEN an administrator creates a user account, THE Platform SHALL require a Role assignment of either security_team or marketing_team before the account is active
2. WHILE a user is authenticated with the security_team Role, THE Platform SHALL grant access to the Security_Dashboard, intelligence APIs (read and write), collector management, manual collection triggers, and read-only access to the Approval_Queue for alert messages
3. WHILE a user is authenticated with the marketing_team Role, THE Platform SHALL grant access to the Marketing_Dashboard, content generation APIs, approval queue, subscriber management, social media publishing, and read-only access to Intel_Items for content generation purposes
4. IF a user with the marketing_team Role attempts to access collector management, trigger collection runs, or modify intelligence data, THEN THE Platform SHALL deny the request and return an authorization error indicating insufficient permissions without revealing details of the protected resource
5. IF a user with the security_team Role attempts to publish content, modify subscriber lists, or invoke content generation endpoints, THEN THE Platform SHALL deny the request and return an authorization error indicating insufficient permissions without revealing details of the protected resource
6. IF a request is made to any protected API endpoint or dashboard route without a valid authenticated session, THEN THE Platform SHALL deny access and redirect the user to the authentication page
7. THE Platform SHALL enforce Role-based access restrictions on both dashboard UI routes and their corresponding API endpoints

### Requirement 11: Background Automation and Scheduling

**User Story:** As a platform operator, I want intelligence collection and processing to run automatically in the background, so that the platform maintains fresh data without requiring manual intervention.

#### Acceptance Criteria

1. THE Background_Scheduler SHALL execute the full collection pipeline (social, advisories, blogs, vulnerabilities, breaches, compliance) at the configured interval, which defaults to 20 minutes and is configurable between 5 and 1440 minutes
2. WHEN a collection cycle completes with at least one pipeline returning new signals, THE Background_Scheduler SHALL trigger the Unified_Intel_Pipeline to group, enrich, score, and classify signals collected since the previous unified pipeline run
3. THE Background_Scheduler SHALL use Celery with Redis as the task broker for job scheduling and execution
4. THE Security_Dashboard SHALL display current job status (running, completed, failed), last execution timestamp in UTC, and next scheduled run time for each collection task, refreshing this information at most every 30 seconds
5. WHEN a security analyst triggers a manual collection run from the Security_Dashboard, THE Background_Scheduler SHALL enqueue the requested pipeline within 5 seconds and execute it independently of the regular schedule
6. IF a background job fails, THEN THE Background_Scheduler SHALL log the error with stack trace and retry the job up to 3 times with exponential backoff starting at 60 seconds (60s, 120s, 240s) before marking it as permanently failed
7. IF a manual collection run is triggered while a scheduled cycle of the same pipeline is already executing, THEN THE Background_Scheduler SHALL queue the manual run to execute after the in-progress cycle completes rather than running both concurrently

### Requirement 12: OSINT Investigation Tools

**User Story:** As a security analyst, I want access to on-demand OSINT investigation tools, so that I can perform deep-dive research on companies, employees, domains, and IP addresses without leaving the platform.

#### Acceptance Criteria

1. THE Intelligence_Service SHALL expose OSINT tools for company scanning (WHOIS, subdomain enumeration, Google dork generation, breach check) via API endpoints that accept a domain name and optional contact email as input and return structured results per tool category
2. THE Intelligence_Service SHALL expose OSINT tools for employee leak detection (HaveIBeenPwned breach lookup, email footprint enumeration, paste dump search) via API endpoints that accept an email address as input and return structured results per tool category
3. THE Intelligence_Service SHALL expose OSINT tools for infrastructure reconnaissance (Shodan host lookup, DNS enumeration, VirusTotal analysis, AbuseIPDB reputation, IP geolocation) via API endpoints that accept an IP address or domain as input and return structured results per tool category
4. WHEN a security analyst initiates a company scan, THE Intelligence_Service SHALL execute all configured company scan tools with a per-tool timeout of 120 seconds, calculate a threat score (0-100) based on the number and severity of discovered exposures (breached credentials, exposed subdomains, dangerous dork matches, WHOIS privacy issues), and store the result
5. IF an external OSINT data source (Shodan, HaveIBeenPwned, VirusTotal, AbuseIPDB, or DeHashed) is unreachable or returns an error during an on-demand scan, THEN THE Intelligence_Service SHALL skip that source, include an error indicator for the failed tool in the response, and return results from the remaining sources
6. WHEN the Intelligence_Service processes an intel item for feed inclusion, THE Intelligence_Service SHALL evaluate the item for misinformation by sending the content and source URL to the configured LLM_Provider and receiving a verdict of LEGITIMATE, MISINFORMATION, or UNVERIFIED with a confidence score (0.0-1.0)
7. IF the misinformation detection verdict is MISINFORMATION with a confidence score above 0.7, THEN THE Intelligence_Service SHALL suppress the item from the main intelligence feed and flag it for manual analyst review

### Requirement 13: Notification and Alerting

**User Story:** As a security analyst, I want to receive alerts when critical threats are detected, so that I can respond to high-severity incidents without constantly monitoring the dashboard.

#### Acceptance Criteria

1. WHEN the SAINT_Engine assigns a risk level of CRITICAL to an Intel_Item, THE Platform SHALL generate an alert notification within 60 seconds containing the Intel_Item title, SAINT confidence score, risk level, primary CVE identifier (if present), affected vendor and product, and a link to the full Intel_Item detail view
2. THE Content_Service SHALL support generating Slack Block Kit alert messages from critical Intel_Items including the Intel_Item title, confidence score, risk level, affected vendor/product, primary CVE, and a summary of no more than 280 characters for distribution to configured channels
3. THE Content_Service SHALL support generating Microsoft Teams message cards from critical Intel_Items including the Intel_Item title, confidence score, risk level, affected vendor/product, primary CVE, and a summary of no more than 280 characters for distribution to configured channels
4. WHEN an alert message is generated and the alert is not configured for auto-send, THE Content_Service SHALL place the message in the Approval_Queue with status PENDING_REVIEW before distribution
5. IF an alert is configured for auto-send, THEN THE Content_Service SHALL distribute the message to the configured channel immediately without placing it in the Approval_Queue
6. IF delivery of an alert message to a configured Slack or Teams channel fails, THEN THE Content_Service SHALL retry delivery up to 3 times with exponential backoff and, if all retries fail, log the failure and display the undelivered alert in the Security_Dashboard with a delivery-failed status

### Requirement 14: Data Migration and Consolidation

**User Story:** As a platform operator, I want existing data from both projects (TinyDB, Lowdb, SQLite) to be migrated into the unified database, so that historical intelligence and marketing assets are preserved in the new system.

#### Acceptance Criteria

1. THE Platform SHALL provide a migration utility that imports existing TinyDB intelligence records from OpenOSINT into the shared PostgreSQL database
2. THE Platform SHALL provide a migration utility that imports existing Lowdb marketing data (campaigns, subscribers, assets) from the Marketing Module into the shared database
3. THE Platform SHALL provide a migration utility that imports existing SQLite records (advisories, blogs, breaches, compliance, social intel, unified intel, vulnerabilities) from Zero Day Radar into the shared database
4. WHEN a migration utility runs, THE Platform SHALL preserve original timestamps (created_at, updated_at), identifiers (record IDs, CVE IDs), and source attribution fields from the source database by mapping them to corresponding columns in the PostgreSQL schema
5. WHEN a migration utility encounters duplicate records (matching by CVE ID, title hash, or source URL), THE Platform SHALL merge the records by retaining the metadata from the record with the most recent updated_at timestamp and appending any distinct source references not already present
6. WHEN a migration utility completes, THE Platform SHALL output a summary report containing the total records read from source, records successfully imported, records skipped due to duplication, records failed, and elapsed time
7. IF a migration utility encounters a record that cannot be imported due to missing required fields or schema incompatibility, THEN THE Platform SHALL skip that record, log the record identifier and failure reason, and continue processing remaining records
8. IF a migration utility is re-run against a source that has already been migrated, THEN THE Platform SHALL skip previously imported records (identified by source database origin and original record ID) without creating duplicates
