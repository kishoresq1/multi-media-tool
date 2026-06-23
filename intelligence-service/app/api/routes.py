import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.keywords import (
    SEARCH_KEYWORDS,
    THREAT_ACTIVITY_KEYWORDS,
    VENDOR_KEYWORDS,
    VULNERABILITY_KEYWORDS,
)
from app.config.sources import SOURCE_REGISTRY, SourceCategory, get_sources_by_category
from app.db.database import get_session
from app.db.models import ScoredPost
from app.db.repository import HuntRepository
from app.db.intel_repository import IntelPostRepository
from app.config.research_blogs import RESEARCH_BLOG_SOURCE_IDS
from app.config.vendor_advisories import VENDOR_ADVISORY_SOURCE_IDS
from app.config.vulnerability_sources import VULNERABILITY_SOURCE_IDS
from app.db.advisory_repository import AdvisoryRepository
from app.db.blog_repository import BlogRepository
from app.db.vulnerability_repository import VulnerabilityRepository
from app.config.company_breach_sources import (
    COMPANY_BREACH_SOURCE_IDS,
    TIER_1_COMPANY_BREACH_SOURCE_IDS,
)
from app.config.compliance_sources import COMPLIANCE_SOURCE_IDS, SOURCE_ORG_MAP, TIER_1_COMPLIANCE_SOURCE_IDS, TIER_2_COMPLIANCE_SOURCE_IDS
from app.db.breach_repository import BreachRepository
from app.config.compliance_scoring import COMPLIANCE_SOURCE_SCORES
from app.db.compliance_repository import ComplianceRepository
from app.models.schemas import (
    AdvisoryIntelResponse,
    AdvisoryListResponse,
    AdvisorySearchRequest,
    AdvisorySearchResponse,
    BlogIntelResponse,
    BlogListResponse,
    BlogSearchRequest,
    BlogSearchResponse,
    BreachIntelResponse,
    BreachListResponse,
    BreachSearchRequest,
    BreachSearchResponse,
    ComplianceIntelResponse,
    ComplianceListResponse,
    ComplianceScoreBreakdown,
    ComplianceScoreRequest,
    ComplianceScoreResponse,
    ComplianceSearchRequest,
    ComplianceSearchResponse,
    HealthResponse,
    HuntRequest,
    HuntResponse,
    IntelPostResponse,
    IntelPostsListResponse,
    PipelineRequest,
    PipelineResponse,
    PipelineRunSummary,
    PostsListResponse,
    ScoredPostResponse,
    SocialSearchRequest,
    SocialSearchResponse,
    SourceInfo,
    ThreatClassificationRequest,
    ThreatClassificationResponse,
    ThreatScoreBreakdown,
    ThreatScoreRequest,
    ThreatScoreResponse,
    VulnerabilityIntelResponse,
    VulnerabilityListResponse,
    VulnerabilitySearchRequest,
    VulnerabilitySearchResponse,
)
from app.services.advisory_search import AdvisorySearchService, advisory_to_response
from app.services.blog_search import BlogSearchService, blog_to_response
from app.services.vulnerability_search import (
    VulnerabilitySearchService,
    vulnerability_to_response,
)
from app.services.breach_search import BreachSearchService, breach_to_response
from app.services.compliance_search import ComplianceSearchService, compliance_to_response
from app.processors.compliance_scoring_engine import ComplianceScoringEngine
from app.processors.threat_classification_engine import ThreatClassificationEngine
from app.processors.threat_scoring_engine import ThreatScoringEngine
from app.config.threat_scoring import THREAT_SOURCE_SCORES
from app.services.hunter import ThreatHunter
from app.services.pipeline import StagedPipeline, db_post_to_response
from app.services.social_search import SocialSearchService, intel_post_to_response

router = APIRouter()
hunter = ThreatHunter()
pipeline = StagedPipeline()
social_search = SocialSearchService()
advisory_search = AdvisorySearchService()
blog_search = BlogSearchService()
vulnerability_search = VulnerabilitySearchService()
breach_search = BreachSearchService()
compliance_search = ComplianceSearchService()
compliance_scoring_engine = ComplianceScoringEngine()
threat_scoring_engine = ThreatScoringEngine()
threat_classification_engine = ThreatClassificationEngine()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    from app.config.settings import settings

    enabled = [s for s in SOURCE_REGISTRY.values() if s.enabled]
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        sources_configured=len(SOURCE_REGISTRY),
        sources_enabled=len(enabled),
        database="sqlite",
    )


@router.get("/health/worker")
async def worker_health() -> dict:
    """Check Redis + Celery background worker connectivity."""
    from app.config.settings import settings

    redis_ok = False
    redis_error: str | None = None
    if settings.celery_enabled:
        try:
            import redis

            client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
            client.ping()
            redis_ok = True
        except Exception as exc:
            redis_error = str(exc)

    return {
        "celery_enabled": settings.celery_enabled,
        "redis_ok": redis_ok,
        "redis_error": redis_error,
        "beat_interval_minutes": settings.celery_beat_interval_minutes,
        "scheduled_task": "zdr.run_all_collections",
    }


# ── Social Search (Step 1) — single intel_posts table ─────────────────


@router.get("/social/queries")
async def preview_search_queries(
    vendors: str | None = Query(default=None, description="Comma-separated vendors, e.g. Fortinet,Cisco"),
    max_queries: int = Query(default=40, ge=5, le=120),
) -> dict:
    """Preview PRIMARY [VENDOR] + [SEARCH_KEYWORD] scraper queries."""
    from app.config.query_builder import build_search_queries

    vendor_list = [v.strip() for v in vendors.split(",")] if vendors else None
    queries = build_search_queries(vendors=vendor_list, max_queries=max_queries)
    return {"total": len(queries), "queries": queries}


@router.post("/social/search", response_model=SocialSearchResponse)
async def search_social_sources(
    request: SocialSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> SocialSearchResponse:
    """
    Search X/Twitter, Reddit, LinkedIn, HackerNews using:
    PRIMARY: [VENDOR] + [SEARCH_KEYWORD] (fallback keywords if no match)

    Searches all platforms using PRIMARY SEARCH_KEYWORDS:
    - X/Twitter via Nitter (no API key)
    - Reddit via PullPush API (no key) + security subreddits
    - HackerNews via Algolia API
    - LinkedIn via search scraper
    Stores latest scored posts in `intel_posts` SQLite table.
    """
    try:
        return await social_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/social/posts", response_model=IntelPostsListResponse)
async def list_intel_posts(
    platform: str | None = Query(default=None, description="twitter | reddit | linkedin | hackernews"),
    min_score: float = Query(default=30, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> IntelPostsListResponse:
    """List scored posts from `intel_posts` table, latest first."""
    repo = IntelPostRepository(session)
    posts_db = await repo.list_posts(platform=platform, min_score=min_score, limit=limit, offset=offset)
    total = await repo.count_posts(platform=platform, min_score=min_score)
    return IntelPostsListResponse(
        total=total,
        posts=[intel_post_to_response(p) for p in posts_db],
    )


@router.get("/social/posts/{post_id}", response_model=IntelPostResponse)
async def get_intel_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> IntelPostResponse:
    repo = IntelPostRepository(session)
    post = await repo.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return intel_post_to_response(post)


# ── Vendor Advisories (Step 2) — vendor_advisory_intel table ──────────


@router.get("/advisories/sources")
async def list_advisory_sources() -> dict:
    """List all configured vendor advisory sources and collection methods."""
    from app.config.sources import SOURCE_REGISTRY

    sources = []
    for sid in VENDOR_ADVISORY_SOURCE_IDS:
        s = SOURCE_REGISTRY.get(sid)
        if s:
            sources.append({
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "primary_method": s.primary_method.value,
                "fallback_method": s.fallback_method.value if s.fallback_method else None,
                "feed_url": s.feed_url,
                "trust_weight": s.trust_weight,
            })
    return {"total": len(sources), "sources": sources}


@router.post("/advisories/search", response_model=AdvisorySearchResponse)
async def search_vendor_advisories(
    request: AdvisorySearchRequest,
    session: AsyncSession = Depends(get_session),
) -> AdvisorySearchResponse:
    """
    Search official vendor security advisories using vendor + vulnerability keywords.

    Sources: MSRC, Cisco, Fortinet, Palo Alto, VMware, Ivanti, Citrix, Juniper,
    Chrome, Adobe, Apple, Oracle, SAP, Atlassian, GitLab, ManageEngine,
    AWS, Google Cloud, Docker, HashiCorp.

    Uses RSS / API / HTML scraper per source. Stores in `vendor_advisory_intel` table.
    """
    try:
        return await advisory_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/advisories", response_model=AdvisoryListResponse)
async def list_vendor_advisories(
    source_id: str | None = Query(default=None, description="e.g. msrc, fortinet_psirt"),
    vendor: str | None = Query(default=None, description="e.g. Fortinet, Microsoft"),
    min_score: float = Query(default=40, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> AdvisoryListResponse:
    """List stored vendor advisories from SQLite, latest first."""
    repo = AdvisoryRepository(session)
    rows = await repo.list_advisories(
        source_id=source_id,
        vendor=vendor,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    total = await repo.count(source_id=source_id, vendor=vendor, min_score=min_score)
    return AdvisoryListResponse(
        total=total,
        advisories=[advisory_to_response(r) for r in rows],
    )


@router.get("/advisories/{advisory_id}", response_model=AdvisoryIntelResponse)
async def get_vendor_advisory(
    advisory_id: str,
    session: AsyncSession = Depends(get_session),
) -> AdvisoryIntelResponse:
    repo = AdvisoryRepository(session)
    row = await repo.get(advisory_id)
    if not row:
        raise HTTPException(status_code=404, detail="Advisory not found")
    return advisory_to_response(row)


# ── Vulnerability Sources (Step 4) — vulnerability_intel table ────────


@router.get("/vulnerabilities/sources")
async def list_vulnerability_sources() -> dict:
    """List CVE Program, NVD, CISA KEV, GitHub, Exploit-DB, Metasploit sources."""
    from app.config.sources import SOURCE_REGISTRY

    sources = []
    for sid in VULNERABILITY_SOURCE_IDS:
        s = SOURCE_REGISTRY.get(sid)
        if s:
            sources.append({
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "primary_method": s.primary_method.value,
                "api_endpoint": s.api_endpoint,
                "feed_url": s.feed_url,
                "trust_weight": s.trust_weight,
            })
    return {"total": len(sources), "sources": sources}


@router.post("/vulnerabilities/search", response_model=VulnerabilitySearchResponse)
async def search_vulnerability_sources(
    request: VulnerabilitySearchRequest,
    session: AsyncSession = Depends(get_session),
) -> VulnerabilitySearchResponse:
    """
    Fetch latest vulnerability intel (last 30 days) from:

    CVE Program, GitHub PoC, Exploit-DB, Metasploit, CISA KEV, NVD.

    Stores in `vulnerability_intel` table (separate from advisories/blogs/social).
    """
    try:
        return await vulnerability_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/vulnerabilities", response_model=VulnerabilityListResponse)
async def list_vulnerability_intel(
    source_id: str | None = Query(default=None, description="e.g. nvd, cisa_kev"),
    cve_id: str | None = Query(default=None, description="e.g. CVE-2024-1234"),
    min_score: float = Query(default=30, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> VulnerabilityListResponse:
    repo = VulnerabilityRepository(session)
    rows = await repo.list_items(
        source_id=source_id,
        cve_id=cve_id,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    total = await repo.count(source_id=source_id, min_score=min_score)
    return VulnerabilityListResponse(
        total=total,
        items=[vulnerability_to_response(r) for r in rows],
    )


@router.get("/vulnerabilities/{item_id}", response_model=VulnerabilityIntelResponse)
async def get_vulnerability_intel(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> VulnerabilityIntelResponse:
    repo = VulnerabilityRepository(session)
    row = await repo.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vulnerability intel not found")
    return vulnerability_to_response(row)


# ── Compliance Intelligence — compliance_intel table ──────────────────


@router.get("/compliance/sources")
async def list_compliance_sources() -> dict:
    """List regulatory, standards, vendor, privacy, and AI governance compliance sources."""
    from app.config.sources import SOURCE_REGISTRY

    sources = []
    for sid in COMPLIANCE_SOURCE_IDS:
        s = SOURCE_REGISTRY.get(sid)
        if s:
            tier = 1 if sid in TIER_1_COMPLIANCE_SOURCE_IDS else (2 if sid in TIER_2_COMPLIANCE_SOURCE_IDS else 2)
            sources.append({
                "id": s.id,
                "name": s.name,
                "organization": SOURCE_ORG_MAP.get(s.id),
                "tier": tier,
                "url": s.url,
                "primary_method": s.primary_method.value,
                "fallback_method": s.fallback_method.value if s.fallback_method else None,
                "feed_url": s.feed_url,
                "trust_weight": s.trust_weight,
            })
    return {"total": len(sources), "sources": sources}


@router.get("/compliance/keywords")
async def list_compliance_keywords() -> dict:
    from app.config.compliance_keywords import (
        AI_GOVERNANCE_KEYWORDS,
        AUDIT_KEYWORDS,
        COMPLIANCE_SEARCH_KEYWORDS,
        FRAMEWORK_KEYWORDS,
        PRIVACY_KEYWORDS,
    )

    return {
        "priority": "compliance search keywords first; privacy/audit/AI/framework as fallback",
        "primary": COMPLIANCE_SEARCH_KEYWORDS,
        "fallback": {
            "privacy": PRIVACY_KEYWORDS,
            "audit": AUDIT_KEYWORDS,
            "ai_governance": AI_GOVERNANCE_KEYWORDS,
            "frameworks": FRAMEWORK_KEYWORDS,
        },
        "tier_1_sources": TIER_1_COMPLIANCE_SOURCE_IDS,
        "tier_2_sources": TIER_2_COMPLIANCE_SOURCE_IDS,
        "source_scores": COMPLIANCE_SOURCE_SCORES,
    }


@router.post("/compliance/score", response_model=ComplianceScoreResponse)
async def score_compliance_cluster(request: ComplianceScoreRequest) -> ComplianceScoreResponse:
    """
    SAINT Compliance Scoring Engine — calculate 0-100 confidence from sources + bonuses.

    Matching is assumed complete; this endpoint only calculates the score.
    """
    payload = request.model_dump()
    payload["signal_count"] = request.signal_count or len(request.sources)
    result = compliance_scoring_engine.score_cluster(payload)
    breakdown = result["score_breakdown"]
    return ComplianceScoreResponse(
        organization_name=result["organization_name"],
        framework_name=result["framework_name"],
        confidence_score=result["confidence_score"],
        risk_level=result["risk_level"],
        score_breakdown=ComplianceScoreBreakdown(**breakdown),
        reason=result["reason"],
    )


@router.post("/compliance/search", response_model=ComplianceSearchResponse)
async def search_compliance_sources(
    request: ComplianceSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> ComplianceSearchResponse:
    """
    Search compliance intel from regulators, standards bodies, vendors, and privacy authorities.

    Extracts framework names, versions, effective dates, deadlines, and impacted controls.
    Tier 1 sources (NIST, ISO, PCI SSC, ENISA, EDPB, CISA, EU AI Act, IAPP) are prioritized.
    Stores in `compliance_intel` table. Returns high-confidence findings by default.
    """
    try:
        return await compliance_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/compliance", response_model=ComplianceListResponse)
async def list_compliance_intel(
    source_id: str | None = Query(default=None, description="e.g. nist_compliance, pci_ssc"),
    organization: str | None = Query(default=None, description="e.g. NIST, PCI SSC"),
    framework: str | None = Query(default=None, description="e.g. ISO 27001, GDPR"),
    source_tier: int | None = Query(default=None, ge=1, le=2, description="1=highest priority"),
    min_score: float = Query(default=50, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ComplianceListResponse:
    """List stored compliance findings, Tier 1 sources first, latest by date."""
    repo = ComplianceRepository(session)
    rows = await repo.list_items(
        source_id=source_id,
        organization=organization,
        framework=framework,
        source_tier=source_tier,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    total = await repo.count(
        source_id=source_id,
        organization=organization,
        source_tier=source_tier,
        min_score=min_score,
    )
    return ComplianceListResponse(
        total=total,
        items=[compliance_to_response(r) for r in rows],
    )


@router.get("/compliance/{item_id}", response_model=ComplianceIntelResponse)
async def get_compliance_intel(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> ComplianceIntelResponse:
    repo = ComplianceRepository(session)
    row = await repo.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Compliance finding not found")
    return compliance_to_response(row)


# ── Company Breach Intel — company_breach_intel table ─────────────────


@router.get("/breaches/sources")
async def list_breach_sources() -> dict:
    """List Tier 1 company breach / ransomware news sources."""
    from app.config.sources import SOURCE_REGISTRY

    sources = []
    for sid in COMPANY_BREACH_SOURCE_IDS:
        s = SOURCE_REGISTRY.get(sid)
        if s:
            sources.append({
                "id": s.id,
                "name": s.name,
                "tier": 1 if sid in TIER_1_COMPANY_BREACH_SOURCE_IDS else 2,
                "url": s.url,
                "primary_method": s.primary_method.value,
                "fallback_method": s.fallback_method.value if s.fallback_method else None,
                "feed_url": s.feed_url,
                "trust_weight": s.trust_weight,
            })
    return {"total": len(sources), "tier_1": TIER_1_COMPANY_BREACH_SOURCE_IDS, "sources": sources}


@router.get("/breaches/keywords")
async def list_breach_keywords() -> dict:
    from app.config.company_breach_keywords import BREACH_SEARCH_KEYWORDS

    return {
        "priority": "Tier 1 breach outlets store all items within lookback; keywords used for tagging",
        "primary": BREACH_SEARCH_KEYWORDS,
        "tier_1_sources": TIER_1_COMPANY_BREACH_SOURCE_IDS,
    }


@router.post("/breaches/search", response_model=BreachSearchResponse)
async def search_company_breaches(
    request: BreachSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> BreachSearchResponse:
    """
    Fetch company breach and ransomware news (last 30 days by default).

    Sources: KrebsOnSecurity, BleepingComputer, SecurityWeek,
    The Hacker News, Ransomware.live.

    RSS with HTML scraper fallback. Stores in `company_breach_intel` table.
    """
    try:
        return await breach_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/breaches", response_model=BreachListResponse)
async def list_company_breaches(
    source_id: str | None = Query(default=None, description="e.g. bleepingcomputer, ransomware_live"),
    breach_type: str | None = Query(default=None, description="ransomware | data_breach | cyberattack"),
    min_score: float = Query(default=0.0, ge=0.0, le=100.0),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> BreachListResponse:
    """List stored company breach intel, Tier 1 first, latest by date."""
    repo = BreachRepository(session)
    rows = await repo.list_items(
        source_id=source_id,
        breach_type=breach_type,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    total = await repo.count(source_id=source_id, breach_type=breach_type, min_score=min_score)
    return BreachListResponse(
        total=total,
        items=[breach_to_response(r) for r in rows],
    )


@router.get("/breaches/{item_id}", response_model=BreachIntelResponse)
async def get_company_breach(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> BreachIntelResponse:
    repo = BreachRepository(session)
    row = await repo.get(item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Breach intel not found")
    return breach_to_response(row)


# ── Researcher Blogs (Step 3) — research_blog_intel table ─────────────


@router.get("/blogs/sources")
async def list_blog_sources() -> dict:
    """List high-trust researcher blog sources and collection methods."""
    from app.config.sources import SOURCE_REGISTRY

    sources = []
    for sid in RESEARCH_BLOG_SOURCE_IDS:
        s = SOURCE_REGISTRY.get(sid)
        if s:
            sources.append({
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "primary_method": s.primary_method.value,
                "fallback_method": s.fallback_method.value if s.fallback_method else "html_scraper",
                "feed_url": s.feed_url,
                "trust_weight": s.trust_weight,
            })
    return {"total": len(sources), "sources": sources}


@router.post("/blogs/search", response_model=BlogSearchResponse)
async def search_research_blogs(
    request: BlogSearchRequest,
    session: AsyncSession = Depends(get_session),
) -> BlogSearchResponse:
    """
    Fetch latest vulnerability research from high-trust blogs.

    Sources: Project Zero, watchTowr, Unit42, DFIR Report,
    Sophos X-Ops, Orange Cyberdefense, SANS ISC, Rapid7, Tenable.

    Uses RSS with HTML scraper fallback. Stores in `research_blog_intel` table.
    """
    try:
        return await blog_search.search_and_store(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/blogs", response_model=BlogListResponse)
async def list_research_blogs(
    source_id: str | None = Query(default=None, description="e.g. project_zero, unit42"),
    min_score: float = Query(default=35, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> BlogListResponse:
    """List stored researcher blog posts, latest first."""
    repo = BlogRepository(session)
    rows = await repo.list_posts(source_id=source_id, min_score=min_score, limit=limit, offset=offset)
    total = await repo.count(source_id=source_id, min_score=min_score)
    return BlogListResponse(total=total, posts=[blog_to_response(r) for r in rows])


@router.get("/blogs/{post_id}", response_model=BlogIntelResponse)
async def get_research_blog_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> BlogIntelResponse:
    repo = BlogRepository(session)
    row = await repo.get(post_id)
    if not row:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return blog_to_response(row)


# ── Staged Pipeline (SQLite) ──────────────────────────────────────────


@router.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(
    request: PipelineRequest,
    session: AsyncSession = Depends(get_session),
) -> PipelineResponse:
    """
    Run the full staged CTI pipeline:

    1. Scrape X/LinkedIn researcher posts → `researcher_social_posts`
    2. Search researcher blogs → `researcher_blog_posts`
    3. Vendor advisories → `vendor_advisory_posts`
    4. CVE/NVD/KEV sources → `cve_findings`
    5. Score & correlate all → `scored_posts` (returned as posts)
    """
    if not request.products:
        raise HTTPException(status_code=400, detail="At least one product keyword required")
    try:
        return await pipeline.run(session, request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipeline/runs", response_model=list[PipelineRunSummary])
async def list_pipeline_runs(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[PipelineRunSummary]:
    repo = HuntRepository(session)
    runs = await repo.list_runs(limit=limit)
    summaries = []
    for run in runs:
        count_result = await session.execute(
            select(func.count())
            .select_from(ScoredPost)
            .where(ScoredPost.hunt_run_id == run.id)
        )
        total_posts = count_result.scalar() or 0
        summaries.append(
            PipelineRunSummary(
                hunt_id=run.id,
                products=json.loads(run.products),
                status=run.status,
                current_stage=run.current_stage,
                started_at=run.started_at,
                completed_at=run.completed_at,
                total_posts=total_posts,
            )
        )
    return summaries


@router.get("/pipeline/runs/{hunt_id}", response_model=PipelineResponse)
async def get_pipeline_run(
    hunt_id: str,
    session: AsyncSession = Depends(get_session),
) -> PipelineResponse:
    repo = HuntRepository(session)
    run = await repo.get_run(hunt_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    posts_db = await repo.get_scored_posts(hunt_run_id=hunt_id, limit=200)
    posts = [db_post_to_response(p) for p in posts_db]

    from app.models.schemas import PipelineStageStats

    stages = []
    if run.stage_stats:
        for val in json.loads(run.stage_stats).values():
            stages.append(PipelineStageStats(**val))

    return PipelineResponse(
        hunt_id=run.id,
        query_products=json.loads(run.products),
        status=run.status,
        current_stage=run.current_stage,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_seconds=(
            (run.completed_at - run.started_at).total_seconds()
            if run.completed_at
            else 0.0
        ),
        stages=stages,
        posts=posts,
        total_posts=len(posts),
    )


# ── Scored Posts (Dashboard) ──────────────────────────────────────────


@router.get("/posts", response_model=PostsListResponse)
async def list_posts(
    hunt_id: str | None = Query(default=None, description="Filter by pipeline run"),
    min_confidence: float = Query(default=50, ge=0, le=100, description="SAINT score 0-100"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PostsListResponse:
    """List scored posts from SQLite for dashboard display."""
    repo = HuntRepository(session)
    posts_db = await repo.get_scored_posts(
        hunt_run_id=hunt_id,
        min_confidence=min_confidence,
        limit=limit,
        offset=offset,
    )

    count_query = select(func.count()).select_from(ScoredPost).where(
        ScoredPost.confidence_score >= min_confidence
    )
    if hunt_id:
        count_query = count_query.where(ScoredPost.hunt_run_id == hunt_id)
    total = (await session.execute(count_query)).scalar() or 0

    return PostsListResponse(
        total=total,
        posts=[db_post_to_response(p) for p in posts_db],
    )


@router.get("/posts/{post_id}", response_model=ScoredPostResponse)
async def get_post(
    post_id: str,
    session: AsyncSession = Depends(get_session),
) -> ScoredPostResponse:
    repo = HuntRepository(session)
    post = await repo.get_scored_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post_to_response(post)


# ── Legacy Hunt (parallel, no DB) ─────────────────────────────────────


@router.post("/hunt", response_model=HuntResponse)
async def run_hunt(request: HuntRequest) -> HuntResponse:
    if not request.products:
        raise HTTPException(status_code=400, detail="At least one product keyword required")
    return await hunter.hunt(request)


@router.get("/hunt/quick", response_model=HuntResponse)
async def quick_hunt(
    product: str = Query(..., description="Vendor/product to hunt"),
    lookback_days: int = Query(default=30, ge=1, le=365),
    min_confidence: float = Query(default=50, ge=0, le=100, description="SAINT score 0-100"),
) -> HuntResponse:
    request = HuntRequest(
        products=[product],
        lookback_days=lookback_days,
        min_confidence=min_confidence,
    )
    return await hunter.hunt(request)


@router.get("/keywords")
async def list_keywords() -> dict:
    return {
        "priority": "search keywords first; vendor/vuln/threat as fallback",
        "primary": SEARCH_KEYWORDS,
        "fallback": {
            "vendors": VENDOR_KEYWORDS,
            "vulnerability": VULNERABILITY_KEYWORDS,
            "threat_activity": THREAT_ACTIVITY_KEYWORDS,
        },
        "threat_source_scores": THREAT_SOURCE_SCORES,
    }


@router.post("/classify", response_model=ThreatClassificationResponse)
async def classify_threat_content(request: ThreatClassificationRequest) -> ThreatClassificationResponse:
    """
    SAINT Cyber Threat Classification Engine.

    Classifies content as PRODUCT_VULNERABILITY, COMPANY_BREACH, or UNKNOWN
    and extracts company, vendor, product, and CVE entities.
    """
    result = threat_classification_engine.classify(
        request.title,
        request.content,
        source_table=request.source_table,
    )
    return ThreatClassificationResponse(**result.to_dict())


@router.post("/threat/score", response_model=ThreatScoreResponse)
async def score_threat_cluster(request: ThreatScoreRequest) -> ThreatScoreResponse:
    """
    SAINT Threat Scoring Engine — calculate 0-100 confidence from sources + bonuses.

    Vendor/product matching is assumed complete; this endpoint only calculates the score.
    """
    payload = request.model_dump()
    payload["signal_count"] = request.signal_count or len(request.sources)
    result = threat_scoring_engine.score_cluster(payload)
    breakdown = result["score_breakdown"]
    return ThreatScoreResponse(
        vendor_name=result["vendor_name"],
        product_name=result["product_name"],
        confidence_score=result["confidence_score"],
        risk_level=result["risk_level"],
        score_breakdown=ThreatScoreBreakdown(**breakdown),
        reason=result["reason"],
    )


@router.get("/sources", response_model=list[SourceInfo])
async def list_sources(
    category: SourceCategory | None = Query(default=None),
) -> list[SourceInfo]:
    sources = get_sources_by_category(category)
    return [
        SourceInfo(
            id=s.id,
            name=s.name,
            category=SourceCategory(s.category.value),
            url=s.url,
            primary_method=s.primary_method,
            fallback_method=s.fallback_method,
            trust_weight=s.trust_weight,
            requires_api_key=s.requires_api_key,
            enabled=s.enabled,
            feed_url=s.feed_url,
        )
        for s in sources
    ]
