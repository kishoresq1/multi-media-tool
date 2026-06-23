from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CollectionMethod(str, Enum):
    API = "api"
    RSS = "rss"
    HTML_SCRAPER = "html_scraper"
    JSON_FEED = "json_feed"
    GITHUB_API = "github_api"


class SourceCategory(str, Enum):
    RESEARCHER_SOCIAL = "researcher_social"
    RESEARCHER_BLOG = "researcher_blog"
    CONFERENCE = "conference"
    VENDOR_ADVISORY = "vendor_advisory"
    VULNERABILITY = "vulnerability"
    DARK_WEB_INTEL = "dark_web_intel"
    COMPLIANCE = "compliance"
    COMPANY_BREACH_INTEL = "company_breach_intel"


class HuntRequest(BaseModel):
    """Request to run a CTI hunt across configured sources."""

    products: list[str] = Field(
        ...,
        min_length=1,
        description="Vendor/product keywords to hunt (e.g. Fortinet, Cisco ISE)",
        examples=[["Fortinet", "Cisco ISE"]],
    )
    source_ids: list[str] | None = Field(
        default=None,
        description="Limit hunt to specific source IDs; null = all enabled sources",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=50, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = Field(
        default=False,
        description="Include findings below min_confidence threshold",
    )
    vulnerability_keywords: list[str] | None = Field(
        default=None,
        description="Override default vulnerability keywords",
    )


class RawSignal(BaseModel):
    """A single collected signal before processing."""

    source_id: str
    source_name: str
    source_category: SourceCategory
    collection_method: CollectionMethod
    title: str
    url: str | None = None
    content: str = ""
    published_at: datetime | None = None
    author: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class ThreatFinding(BaseModel):
    """Processed, scored threat intelligence finding."""

    id: str
    title: str
    url: str | None = None
    summary: str = ""
    published_at: datetime | None = None

    # Extracted intelligence
    vendors: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)
    vulnerability_types: list[str] = Field(default_factory=list)
    threat_indicators: list[str] = Field(default_factory=list)

    # Flags
    has_poc: bool = False
    active_exploitation: bool = False
    in_cisa_kev: bool = False
    is_vendor_advisory: bool = False

    # Scoring (SAINT 0-100)
    confidence_score: float = Field(ge=0.0, le=100.0)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = Field(ge=0.0, le=100.0, default=0.0)
    recency_score: float = Field(ge=0.0, le=100.0, default=0.0)
    keyword_match_score: float = Field(ge=0.0, le=100.0, default=0.0)

    # Provenance
    sources: list[str] = Field(default_factory=list)
    source_categories: list[SourceCategory] = Field(default_factory=list)
    collection_methods: list[CollectionMethod] = Field(default_factory=list)
    correlated_count: int = 1
    is_duplicate: bool = False

    matched_keywords: list[str] = Field(default_factory=list)
    matched_products: list[str] = Field(default_factory=list)


class HuntStats(BaseModel):
    sources_queried: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    raw_signals_collected: int = 0
    findings_before_dedup: int = 0
    findings_after_dedup: int = 0
    high_confidence_findings: int = 0
    failed_sources: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0


class HuntResponse(BaseModel):
    hunt_id: str
    query_products: list[str]
    started_at: datetime
    completed_at: datetime
    stats: HuntStats
    findings: list[ThreatFinding]


class SourceInfo(BaseModel):
    id: str
    name: str
    category: SourceCategory
    url: str
    primary_method: CollectionMethod
    fallback_method: CollectionMethod | None = None
    trust_weight: float
    requires_api_key: bool
    enabled: bool
    feed_url: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    sources_configured: int
    sources_enabled: int
    database: str = "sqlite"


class PipelineRequest(BaseModel):
    """Run the staged SQLite pipeline: social → blogs → advisories → CVE → score."""

    products: list[str] = Field(
        ...,
        min_length=1,
        examples=[["Fortinet", "Cisco ISE"]],
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=50, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = False
    vulnerability_keywords: list[str] | None = None


class PipelineStageStats(BaseModel):
    stage: int
    name: str
    sources_queried: int = 0
    records_saved: int = 0
    sources_failed: int = 0


class ScoredPostResponse(BaseModel):
    """Final scored post for dashboard display."""

    id: str
    hunt_run_id: str
    title: str
    summary: str = ""
    url: str | None = None
    published_at: datetime | None = None

    vendors: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)
    vulnerability_types: list[str] = Field(default_factory=list)
    threat_indicators: list[str] = Field(default_factory=list)

    has_poc: bool = False
    active_exploitation: bool = False
    in_cisa_kev: bool = False
    is_vendor_advisory: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    recency_score: float = 0.0
    keyword_match_score: float = 0.0

    sources: list[str] = Field(default_factory=list)
    source_categories: list[str] = Field(default_factory=list)
    stage_sources: list[str] = Field(default_factory=list)
    correlated_count: int = 1
    matched_keywords: list[str] = Field(default_factory=list)
    matched_products: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class PipelineResponse(BaseModel):
    hunt_id: str
    query_products: list[str]
    status: str
    current_stage: int
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    stages: list[PipelineStageStats] = Field(default_factory=list)
    posts: list[ScoredPostResponse] = Field(default_factory=list)
    total_posts: int = 0


class PipelineRunSummary(BaseModel):
    hunt_id: str
    products: list[str]
    status: str
    current_stage: int
    started_at: datetime
    completed_at: datetime | None = None
    total_posts: int = 0


class PostsListResponse(BaseModel):
    total: int
    posts: list[ScoredPostResponse]


class SocialSearchRequest(BaseModel):
    """Search social sources using [VENDOR] + [VULNERABILITY KEYWORD]."""

    vendors: list[str] | None = Field(
        default=None,
        description="Vendor keywords to search. Null = all configured vendors.",
        examples=[["Fortinet", "Cisco", "VMware"]],
    )
    sources: list[str] | None = Field(
        default=None,
        description="Sources to search: twitter, reddit, hackernews, linkedin",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    max_queries: int = Field(default=40, ge=5, le=120)
    min_confidence: float = Field(default=30, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = False
    result_limit: int = Field(default=50, ge=1, le=200)


class IntelPostResponse(BaseModel):
    id: str
    platform: str
    source_name: str
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    search_query: str | None = None

    matched_vendors: list[str] = Field(default_factory=list)
    matched_vuln_keywords: list[str] = Field(default_factory=list)
    matched_threat_keywords: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)

    has_poc: bool = False
    active_exploitation: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    threat_score: float = 0.0
    created_at: datetime | None = None


class SocialSearchResponse(BaseModel):
    search_id: str
    queries_used: int
    sources_searched: list[str]
    source_stats: dict[str, dict]
    posts_found: int
    posts_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    posts: list[IntelPostResponse] = Field(default_factory=list)


class IntelPostsListResponse(BaseModel):
    total: int
    posts: list[IntelPostResponse]


class AdvisorySearchRequest(BaseModel):
    """Search vendor advisories using vendor + vulnerability keywords."""

    vendors: list[str] | None = Field(
        default=None,
        description="Filter by vendors. Null = all configured vendors.",
        examples=[["Fortinet", "Microsoft", "Cisco"]],
    )
    source_ids: list[str] | None = Field(
        default=None,
        description="Limit to specific advisory source IDs (msrc, fortinet_psirt, etc.)",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=40, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = False
    result_limit: int = Field(default=100, ge=1, le=500)


class AdvisoryIntelResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    vendor: str | None = None
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    published_at: datetime | None = None

    matched_vendors: list[str] = Field(default_factory=list)
    matched_vuln_keywords: list[str] = Field(default_factory=list)
    matched_threat_keywords: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)
    severity: str | None = None

    has_poc: bool = False
    active_exploitation: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    created_at: datetime | None = None


class AdvisorySearchResponse(BaseModel):
    search_id: str
    sources_searched: list[str]
    source_stats: dict[str, dict]
    advisories_found: int
    advisories_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    advisories: list[AdvisoryIntelResponse] = Field(default_factory=list)


class AdvisoryListResponse(BaseModel):
    total: int
    advisories: list[AdvisoryIntelResponse]


class BlogSearchRequest(BaseModel):
    """Search high-trust researcher blogs for vulnerability updates."""

    vendors: list[str] | None = Field(
        default=None,
        description="Filter by vendor/product keywords. Null = all vulnerability posts.",
        examples=[["Fortinet", "Cisco", "VMware"]],
    )
    source_ids: list[str] | None = Field(
        default=None,
        description="Limit to blog source IDs (project_zero, unit42, etc.)",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=35, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = False
    result_limit: int = Field(default=100, ge=1, le=500)


class BlogIntelResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None

    matched_vendors: list[str] = Field(default_factory=list)
    matched_vuln_keywords: list[str] = Field(default_factory=list)
    matched_threat_keywords: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)

    has_poc: bool = False
    active_exploitation: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    created_at: datetime | None = None


class BlogSearchResponse(BaseModel):
    search_id: str
    sources_searched: list[str]
    source_stats: dict[str, dict]
    posts_found: int
    posts_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    posts: list[BlogIntelResponse] = Field(default_factory=list)


class BlogListResponse(BaseModel):
    total: int
    posts: list[BlogIntelResponse]


class BreachSearchRequest(BaseModel):
    """Fetch company breach / ransomware news from Tier 1 outlets."""

    source_ids: list[str] | None = Field(
        default=None,
        description="Limit to breach source IDs (krebsonsecurity, bleepingcomputer, etc.)",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=30, ge=0, le=100)
    include_low_confidence: bool = False
    result_limit: int = Field(default=200, ge=1, le=500)


class BreachIntelResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    source_tier: int = 1
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None

    affected_company: str | None = None
    breach_type: str | None = None

    matched_breach_keywords: list[str] = Field(default_factory=list)
    matched_vendors: list[str] = Field(default_factory=list)
    matched_vuln_keywords: list[str] = Field(default_factory=list)
    matched_threat_keywords: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)

    has_poc: bool = False
    active_exploitation: bool = False
    is_ransomware: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    created_at: datetime | None = None


class BreachSearchResponse(BaseModel):
    search_id: str
    sources_searched: list[str]
    source_stats: dict[str, dict]
    items_found: int
    items_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items: list[BreachIntelResponse] = Field(default_factory=list)


class BreachListResponse(BaseModel):
    total: int
    items: list[BreachIntelResponse]


class VulnerabilitySearchRequest(BaseModel):
    """Fetch vulnerability intel from CVE/NVD/KEV/GitHub/Exploit-DB/Metasploit."""

    source_ids: list[str] | None = Field(
        default=None,
        description="Limit to source IDs (cve_program, nvd, cisa_kev, github_poc, exploit_db, metasploit)",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(default=30, ge=0, le=100, description="SAINT score threshold 0-100")
    include_low_confidence: bool = False
    result_limit: int = Field(default=200, ge=1, le=1000)


class VulnerabilityIntelResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None

    cve_id: str | None = None
    cvss_score: float | None = None
    severity: str | None = None

    matched_vendors: list[str] = Field(default_factory=list)
    matched_vuln_keywords: list[str] = Field(default_factory=list)
    matched_threat_keywords: list[str] = Field(default_factory=list)
    cves: list[str] = Field(default_factory=list)

    in_cisa_kev: bool = False
    has_poc: bool = False
    has_exploit: bool = False
    active_exploitation: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    created_at: datetime | None = None


class VulnerabilitySearchResponse(BaseModel):
    search_id: str
    sources_searched: list[str]
    source_stats: dict[str, dict]
    items_found: int
    items_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items: list[VulnerabilityIntelResponse] = Field(default_factory=list)


class VulnerabilityListResponse(BaseModel):
    total: int
    items: list[VulnerabilityIntelResponse]


class ComplianceSearchRequest(BaseModel):
    """Search compliance sources for framework updates and new requirements."""

    frameworks: list[str] | None = Field(
        default=None,
        description="Filter by frameworks (ISO 27001, PCI DSS, GDPR, etc.). Null = all.",
        examples=[["ISO 27001", "PCI DSS", "GDPR"]],
    )
    source_ids: list[str] | None = Field(
        default=None,
        description="Limit to compliance source IDs (nist_compliance, pci_ssc, edpb, etc.)",
    )
    source_tier: int | None = Field(
        default=None,
        ge=1,
        le=2,
        description="1 = regulators/standards bodies, 2 = vendor compliance",
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    min_confidence: float = Field(
        default=50,
        ge=0,
        le=100,
        description="SAINT compliance score threshold (0-100)",
    )
    include_low_confidence: bool = False
    result_limit: int = Field(default=100, ge=1, le=500)


class ComplianceIntelResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    organization: str | None = None
    source_tier: int = 2
    source_subtype: str = "regulatory"
    collection_method: str
    title: str
    content: str = ""
    url: str | None = None
    author: str | None = None
    published_at: datetime | None = None

    matched_compliance_keywords: list[str] = Field(default_factory=list)
    matched_privacy_keywords: list[str] = Field(default_factory=list)
    matched_audit_keywords: list[str] = Field(default_factory=list)
    matched_ai_keywords: list[str] = Field(default_factory=list)
    matched_framework_keywords: list[str] = Field(default_factory=list)

    frameworks: list[str] = Field(default_factory=list)
    framework_versions: list[str] = Field(default_factory=list)
    effective_dates: list[str] = Field(default_factory=list)
    compliance_deadlines: list[str] = Field(default_factory=list)
    impacted_controls: list[str] = Field(default_factory=list)

    is_new_requirement: bool = False
    is_framework_update: bool = False

    confidence_score: float = Field(default=0.0, ge=0, le=100, description="SAINT score 0-100")
    risk_level: str = "LOW"
    score_breakdown: dict = Field(default_factory=dict)
    score_reason: str = ""
    source_trust_score: float = 0.0
    keyword_match_score: float = 0.0
    recency_score: float = 0.0
    created_at: datetime | None = None


class ComplianceSearchResponse(BaseModel):
    search_id: str
    sources_searched: list[str]
    source_stats: dict[str, dict]
    items_found: int
    items_saved: int
    total_in_database: int
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    items: list[ComplianceIntelResponse] = Field(default_factory=list)


class ComplianceListResponse(BaseModel):
    total: int
    items: list[ComplianceIntelResponse]


class ComplianceSourceInput(BaseModel):
    source_id: str | None = None
    source_type: str | None = None
    source_name: str


class ComplianceScoreRequest(BaseModel):
    """SAINT Compliance Scoring Engine input — matching only assumed done."""

    organization_name: str = ""
    framework_name: str = ""
    sources: list[ComplianceSourceInput] = Field(..., min_length=1)
    framework_update: bool = False
    new_requirement: bool = False
    effective_date_present: bool = False
    deadline_present: bool = False
    controls_impacted: bool = False
    framework_identified: bool = False
    version_extracted: bool = False
    signal_count: int = Field(default=1, ge=1)


class ComplianceScoreBreakdown(BaseModel):
    source_score: int = 0
    bonus_score: int = 0
    source_details: list[dict] = Field(default_factory=list)
    bonus_details: list[str] = Field(default_factory=list)
    raw_total: int = 0


class ComplianceScoreResponse(BaseModel):
    organization_name: str = ""
    framework_name: str = ""
    confidence_score: int = Field(ge=0, le=100)
    risk_level: str
    score_breakdown: ComplianceScoreBreakdown
    reason: str = ""


class ThreatSourceInput(BaseModel):
    source_id: str | None = None
    source_type: str | None = None
    source_name: str


class ThreatScoreRequest(BaseModel):
    """SAINT Threat Scoring Engine input — matching assumed complete."""

    vendor_name: str = ""
    product_name: str = ""
    sources: list[ThreatSourceInput] = Field(..., min_length=1)
    cve_present: bool = False
    poc_available: bool = False
    actively_exploited: bool = False
    signal_count: int = Field(default=1, ge=1)


class ThreatScoreBreakdown(BaseModel):
    source_score: int = 0
    bonus_score: int = 0
    source_details: list[dict] = Field(default_factory=list)
    bonus_details: list[str] = Field(default_factory=list)
    raw_total: int = 0


class ThreatScoreResponse(BaseModel):
    vendor_name: str = ""
    product_name: str = ""
    confidence_score: int = Field(ge=0, le=100)
    risk_level: str
    score_breakdown: ThreatScoreBreakdown
    reason: str = ""


class UnifiedRunRequest(BaseModel):
    """Run all collectors then consolidate into unified_intel via Ollama + SAINT scoring."""

    lookback_days: int = Field(default=30, ge=1, le=365)
    run_collections: bool = Field(default=True, description="Run all 5 intel search APIs first")
    use_llm: bool = Field(default=True, description="Enrich with Ollama if available")
    replace_existing: bool = Field(default=False, description="Clear unified_intel before insert")
    min_confidence: float = Field(default=30, ge=0, le=100)
    include_low_confidence: bool = False
    result_limit: int = Field(default=100, ge=1, le=500)


class ThreatClassificationRequest(BaseModel):
    """SAINT incident type classification for raw intelligence text."""

    title: str = Field(..., min_length=1)
    content: str = ""
    source_table: str | None = Field(
        default=None,
        description="Optional source table hint, e.g. vulnerability_intel, company_breach_intel",
    )


class ThreatClassificationResponse(BaseModel):
    incident_type: str = Field(description="PRODUCT_VULNERABILITY | COMPANY_BREACH | UNKNOWN")
    classification_confidence: int = Field(ge=0, le=100)
    company_name: str = ""
    vendor_name: str = ""
    product_name: str = ""
    cve: str = ""
    incident_title: str = ""
    reason: str = ""


class UnifiedIntelResponse(BaseModel):
    id: str
    company_name: str | None = None
    vendor_name: str = ""
    product_name: str = ""
    version_name: str | None = None
    latest_date: datetime | None = None
    title: str
    summary: str = ""
    cves: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    threat_score: float = 0.0
    compliance_score: float = 0.0
    confidence_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: str = "LOW"
    classification: str | None = Field(
        default=None,
        description="PRODUCT_VULNERABILITY | COMPANY_BREACH | UNKNOWN",
    )
    classification_confidence: float = Field(default=0.0, ge=0, le=100)
    classification_reason: str | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_reason: str = ""
    source_count: int = 0
    source_refs: list[dict] = Field(default_factory=list)
    llm_summary: str | None = None
    llm_model: str | None = None
    llm_enriched: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UnifiedListResponse(BaseModel):
    total: int
    items: list[UnifiedIntelResponse]


class UnifiedRunResponse(BaseModel):
    run_id: str
    collections_ran: bool
    collection_stats: dict[str, Any] = Field(default_factory=dict)
    source_records_loaded: int = 0
    clusters_processed: int = 0
    items_saved: int = 0
    total_in_database: int = 0
    ollama_used: bool = False
    ollama_model: str | None = None
    started_at: datetime
    completed_at: datetime
    duration_seconds: float = 0.0
    items: list[UnifiedIntelResponse] = Field(default_factory=list)
