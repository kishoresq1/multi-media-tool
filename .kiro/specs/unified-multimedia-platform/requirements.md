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

1. THE Intelligence_Service SHALL expose all threat intelligence endpoints (collection, scoring, enrichment, unified intel, vulnerabilities, advisories, breaches, compliance, social intel) under a versioned API prefix
2. THE Content_Service SHALL expose all content generation endpoints (email campaigns, HyperFrame visuals, Remotion videos, LinkedIn posts, Slack/Teams alerts, subscriber management) under a versioned API prefix
3. WHEN the Marketing_Dashboard requests intelligence data for content generation, THE Intelligence_Service SHALL return Intel_Items in a format compatible with the Content_Service input schema
4. THE Platform SHALL use a shared PostgreSQL database for intelligence data accessible by both services
5. WHEN the Content_Service generates content from an Intel_Item, THE Intelligence_Service SHALL mark that item as used in marketing upon confirmation

### Requirement 2: Multi-Source Intelligence Collection

**User Story:** As a security analyst, I want the platform to automatically collect threat intelligence from all configured sources, so that I have comprehensive visibility into the threat landscape without manual monitoring.

#### Acceptance Criteria

1. THE Collector SHALL support fetching from RSS feeds, HTML-scraped research blogs, vendor advisories (Microsoft MSRC, Cisco, Fortinet), CVE Program, NVD, exploit databases, and social sources (Reddit, Twitter/Nitter, LinkedIn, HackerNews)
2. THE Collector SHALL support fetching from compliance sources (NIST frameworks, ISO updates, regulatory feeds)
3. WHEN a collection cycle completes, THE Intelligence_Service SHALL store each new signal with source attribution, timestamp, and raw content in the shared database
4. THE Background_Scheduler SHALL execute collection jobs at a configurable interval with a default of 20 minutes
5. IF a Collector source is unreachable or returns an error, THEN THE Intelligence_Service SHALL log the failure, skip that source, and continue collecting from remaining sources without interrupting the cycle
6. WHEN the Intelligence_Service polls NVD and CISA Known Exploited Vulnerabilities feeds, THE Intelligence_Service SHALL deduplicate entries by CVE identifier before storage

### Requirement 3: SAINT Threat Scoring and Classification

**User Story:** As a security analyst, I want collected intelligence to be automatically scored and classified, so that I can prioritize the most critical threats without manually triaging every signal.

#### Acceptance Criteria

1. WHEN the Unified_Intel_Pipeline processes collected signals, THE SAINT_Engine SHALL calculate a threat confidence score from 0 to 100 based on source credibility, corroboration count, CVE presence, proof-of-concept availability, and active exploitation status
2. WHEN the Unified_Intel_Pipeline processes compliance-related signals, THE SAINT_Engine SHALL calculate a separate compliance score from 0 to 100 based on framework identification, regulatory source authority, and update significance
3. THE SAINT_Engine SHALL classify each unified intel record as PRODUCT_VULNERABILITY, COMPANY_BREACH, or UNKNOWN based on content analysis, source table origin, and entity extraction
4. WHEN a cluster has signals from three or more independent sources with active exploitation confirmed, THE SAINT_Engine SHALL assign a risk level of CRITICAL
5. THE Unified_Intel_Pipeline SHALL group related signals by vendor, product, version, and CVE identifiers before scoring

### Requirement 4: LLM-Powered Intelligence Enrichment

**User Story:** As a security analyst, I want collected signals to be enriched with structured metadata extracted by AI, so that I can search and filter intelligence by vendor, product, and version without relying on inconsistent source formatting.

#### Acceptance Criteria

1. WHEN the Unified_Intel_Pipeline processes a signal cluster, THE Intelligence_Service SHALL send cluster context to the configured LLM_Provider for entity extraction (vendor_name, product_name, version_name, primary_cve, summary)
2. IF the configured LLM_Provider (Ollama) is unavailable, THEN THE Intelligence_Service SHALL proceed with rule-based extraction from existing metadata and skip LLM enrichment
3. THE Intelligence_Service SHALL support Ollama as the local LLM_Provider for enrichment with configurable model, base URL, and timeout settings
4. WHEN LLM enrichment completes, THE Intelligence_Service SHALL store the extracted metadata alongside the original signal data and mark the record as LLM-enriched

### Requirement 5: Security Team Dashboard

**User Story:** As a security analyst, I want a dedicated dashboard showing real-time threat intelligence with scoring, filtering, and drill-down capabilities, so that I can monitor the threat landscape and respond to critical issues.

#### Acceptance Criteria

1. THE Security_Dashboard SHALL display a live intelligence feed sorted by latest date and confidence score, with items color-coded by risk level (Critical, High, Medium, Low)
2. THE Security_Dashboard SHALL provide filtering by classification (PRODUCT_VULNERABILITY, COMPANY_BREACH), vendor, product, minimum confidence score, and date range
3. THE Security_Dashboard SHALL display dedicated views for Advisories, Research Blogs, Breaches, Compliance updates, Social Intelligence, and Vulnerabilities
4. THE Security_Dashboard SHALL display a source management interface where analysts can view configured collectors, their last-run status, and enable or disable individual sources
5. WHEN a security analyst selects an Intel_Item, THE Security_Dashboard SHALL display the full detail including SAINT score breakdown, source references, LLM enrichment data, CVE list, and classification reasoning
6. THE Security_Dashboard SHALL display a jobs management view showing background collection task status, last execution time, and the ability to trigger manual collection runs

### Requirement 6: Marketing Team Dashboard

**User Story:** As a marketing team member, I want a dedicated dashboard for creating and managing security-focused marketing content, so that I can produce campaigns, visuals, and social posts from vetted intelligence without needing direct access to the security tools.

#### Acceptance Criteria

1. THE Marketing_Dashboard SHALL display an intel queue showing Intel_Items that have not yet been used in marketing, sorted by severity and recency
2. THE Marketing_Dashboard SHALL provide a campaign builder interface where marketers can select Intel_Items and generate email campaigns using AI assistance
3. THE Marketing_Dashboard SHALL provide a HyperFrame Studio for generating visual content cards (PNG) from Intel_Items with configurable color schemes and layouts
4. THE Marketing_Dashboard SHALL provide a video composer using Remotion for generating video content from Intel_Items
5. THE Marketing_Dashboard SHALL provide a LinkedIn posting interface with post preview, image/video card attachment, and commentary editing
6. THE Marketing_Dashboard SHALL provide a communications panel for composing Slack Block Kit and Microsoft Teams message cards from Intel_Items
7. THE Marketing_Dashboard SHALL provide an asset gallery displaying all previously generated Content_Assets with download and reuse capabilities
8. THE Marketing_Dashboard SHALL provide a subscriber management interface for managing email distribution lists

### Requirement 7: Human-in-the-Loop Content Approval

**User Story:** As a team lead, I want all AI-generated content to require explicit human approval before publishing or distribution, so that the organization maintains quality control and avoids distributing incorrect or inappropriate communications.

#### Acceptance Criteria

1. WHEN the Content_Service generates a Content_Asset (email, visual, video, social post, or alert message), THE Content_Service SHALL place the asset in the Approval_Queue with status PENDING_REVIEW
2. THE Marketing_Dashboard SHALL display the Approval_Queue with preview capabilities for each pending Content_Asset
3. WHEN a human reviewer approves a Content_Asset, THE Content_Service SHALL update the asset status to APPROVED and enable the publish action
4. WHEN a human reviewer rejects a Content_Asset, THE Content_Service SHALL update the asset status to REJECTED and retain the asset with reviewer notes for reference
5. IF a LinkedIn post request does not include human_verified set to true, THEN THE Content_Service SHALL reject the post with an error indicating human review is required
6. WHEN a human reviewer edits a Content_Asset before approval, THE Content_Service SHALL store both the original AI-generated version and the human-edited version

### Requirement 8: AI-Assisted Content Generation

**User Story:** As a marketing team member, I want AI to generate draft content from intelligence items, so that I can produce professional campaigns faster while still controlling the final output.

#### Acceptance Criteria

1. WHEN a marketer requests email generation from an Intel_Item, THE Content_Service SHALL produce a complete email campaign with subject, preheader, headline, body, call-to-action text, recommended action, tone classification, and template type
2. WHEN a marketer requests a HyperFrame visual from an Intel_Item, THE Content_Service SHALL produce a visual content specification with headline, subheadline, body text, severity label, CVE badge, hashtags, call-to-action, color scheme, and stat highlight
3. WHEN a marketer requests a video from an Intel_Item, THE Content_Service SHALL produce a Remotion video composition with scene breakdown, narration text, and visual assets
4. THE Content_Service SHALL support multiple LLM_Providers (Anthropic Claude, OpenAI, OpenRouter, Gemini) for content generation with automatic provider detection based on configured API keys
5. IF the configured LLM_Provider is unavailable, THEN THE Content_Service SHALL generate content using deterministic fallback templates that produce valid output without AI assistance

### Requirement 9: Social Media Publishing (LinkedIn)

**User Story:** As a marketing team member, I want to publish approved intelligence posts to LinkedIn with attached media, so that the organization can share threat awareness content with its professional network.

#### Acceptance Criteria

1. THE Platform SHALL support LinkedIn OAuth 2.0 authentication for personal profile posting
2. WHEN a marketer requests a LinkedIn post, THE Content_Service SHALL generate a post preview with commentary text, and optionally an image card (PNG) or video card (MP4) rendered from the Intel_Item
3. WHEN a marketer confirms a LinkedIn post with human_verified set to true, THE Content_Service SHALL publish the post to the authenticated LinkedIn profile using the LinkedIn Share API
4. THE Marketing_Dashboard SHALL display LinkedIn connection status, display name, and posting mode
5. IF the LinkedIn OAuth token is expired or missing, THEN THE Content_Service SHALL redirect the user to re-authenticate before allowing post operations

### Requirement 10: Role-Based Access Control

**User Story:** As a platform administrator, I want users to access only their team's dashboard and relevant API endpoints, so that security analysts do not accidentally modify marketing content and marketers cannot alter intelligence collection settings.

#### Acceptance Criteria

1. THE Platform SHALL assign each user a Role of security_team or marketing_team upon account creation
2. WHILE a user is authenticated with the security_team Role, THE Platform SHALL grant access to the Security_Dashboard, intelligence APIs, collector management, and manual collection triggers
3. WHILE a user is authenticated with the marketing_team Role, THE Platform SHALL grant access to the Marketing_Dashboard, content generation APIs, approval queue, subscriber management, and social media publishing
4. IF a user with the marketing_team Role attempts to access collector management or modify intelligence data, THEN THE Platform SHALL return an authorization error and deny the request
5. IF a user with the security_team Role attempts to publish content or modify subscriber lists, THEN THE Platform SHALL return an authorization error and deny the request

### Requirement 11: Background Automation and Scheduling

**User Story:** As a platform operator, I want intelligence collection and processing to run automatically in the background, so that the platform maintains fresh data without requiring manual intervention.

#### Acceptance Criteria

1. THE Background_Scheduler SHALL execute the full collection pipeline (social, advisories, blogs, vulnerabilities, breaches, compliance) at the configured interval (default 20 minutes)
2. WHEN a collection cycle completes, THE Background_Scheduler SHALL trigger the Unified_Intel_Pipeline to group, enrich, score, and classify newly collected signals
3. THE Background_Scheduler SHALL use Celery with Redis as the task broker for job scheduling and execution
4. THE Security_Dashboard SHALL display current job status (running, completed, failed), last execution timestamp, and next scheduled run for each collection task
5. WHEN a security analyst triggers a manual collection run from the Security_Dashboard, THE Background_Scheduler SHALL execute the requested pipeline immediately outside the regular schedule
6. IF a background job fails, THEN THE Background_Scheduler SHALL log the error with stack trace and retry the job up to 3 times with exponential backoff before marking it as failed

### Requirement 12: OSINT Investigation Tools

**User Story:** As a security analyst, I want access to on-demand OSINT investigation tools, so that I can perform deep-dive research on companies, employees, domains, and IP addresses without leaving the platform.

#### Acceptance Criteria

1. THE Intelligence_Service SHALL expose OSINT tools for company scanning (WHOIS, subdomain enumeration, Google dork generation, breach check) via API endpoints
2. THE Intelligence_Service SHALL expose OSINT tools for employee leak detection (HaveIBeenPwned breach lookup, email footprint enumeration, paste dump search) via API endpoints
3. THE Intelligence_Service SHALL expose OSINT tools for infrastructure reconnaissance (Shodan host lookup, DNS enumeration, VirusTotal analysis, AbuseIPDB reputation, IP geolocation) via API endpoints
4. WHEN a security analyst initiates a company scan, THE Intelligence_Service SHALL calculate a threat score (0-100) based on discovered exposures and store the result
5. THE Intelligence_Service SHALL support misinformation detection by analyzing claims against source credibility and AI assessment before surfacing items in the feed

### Requirement 13: Notification and Alerting

**User Story:** As a security analyst, I want to receive alerts when critical threats are detected, so that I can respond to high-severity incidents without constantly monitoring the dashboard.

#### Acceptance Criteria

1. WHEN the SAINT_Engine assigns a risk level of CRITICAL to an Intel_Item, THE Platform SHALL generate an alert notification for the security team
2. THE Content_Service SHALL support generating Slack Block Kit alert messages from critical Intel_Items for distribution to configured channels
3. THE Content_Service SHALL support generating Microsoft Teams message cards from critical Intel_Items for distribution to configured channels
4. WHEN an alert message is generated, THE Content_Service SHALL place the message in the Approval_Queue before distribution unless the alert is configured for auto-send

### Requirement 14: Data Migration and Consolidation

**User Story:** As a platform operator, I want existing data from both projects (TinyDB, Lowdb, SQLite) to be migrated into the unified database, so that historical intelligence and marketing assets are preserved in the new system.

#### Acceptance Criteria

1. THE Platform SHALL provide a migration utility that imports existing TinyDB intelligence records from OpenOSINT into the shared PostgreSQL database
2. THE Platform SHALL provide a migration utility that imports existing Lowdb marketing data (campaigns, subscribers, assets) from the Marketing Module into the shared database
3. THE Platform SHALL provide a migration utility that imports existing SQLite records (advisories, blogs, breaches, compliance, social intel, unified intel, vulnerabilities) from Zero Day Radar into the shared database
4. WHEN a migration utility runs, THE Platform SHALL preserve original timestamps, identifiers, and source attribution from the source database
5. WHEN a migration utility encounters duplicate records (matching by CVE ID, title hash, or source URL), THE Platform SHALL merge the records by retaining the most recent metadata and combining source references
