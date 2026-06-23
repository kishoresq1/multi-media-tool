import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.registry import get_collector_for_source
from app.config.keywords import SEARCH_KEYWORDS, VULNERABILITY_KEYWORDS
from app.config.sources import SourceCategory, get_enabled_sources
from app.db.repository import HuntRepository
from app.services.score_fields import normalize_min_score
from app.models.schemas import (
    CollectionMethod,
    PipelineRequest,
    PipelineResponse,
    PipelineStageStats,
    RawSignal,
    ScoredPostResponse,
    SourceCategory as SchemaSourceCategory,
    ThreatFinding,
)
from app.processors.correlator import Correlator
from app.processors.extractor import SignalExtractor
from app.processors.scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

STAGE_SOCIAL = 1
STAGE_BLOG = 2
STAGE_ADVISORY = 3
STAGE_CVE = 4
STAGE_SCORE = 5

SOCIAL_SOURCE_IDS = ["twitter", "linkedin"]
BLOG_SOURCE_IDS = [
    "project_zero", "krebsonsecurity", "watchtowr", "unit42", "dfir_report",
    "sophos_xops", "orange_cyberdefense", "sans_isc", "rapid7", "tenable",
]
ADVISORY_SOURCE_IDS = [
    "msrc", "cisco_advisories", "fortinet_psirt", "palo_alto_advisories",
    "vmware_advisories", "ivanti_advisories", "citrix_bulletins",
    "juniper_advisories", "chrome_releases", "adobe_security", "apple_security",
    "oracle_security", "atlassian_security", "gitlab_security",
    "manageengine_security", "aws_security", "gcp_security", "docker_security",
    "hashicorp_security",
]
CVE_SOURCE_IDS = [
    "cisa_kev", "nvd", "github_poc", "exploit_db", "metasploit", "packetstorm",
]


class StagedPipeline:
    """
    Sequential CTI pipeline stored in SQLite:

    Stage 1 → Scrape X/LinkedIn researcher posts → researcher_social_posts
    Stage 2 → Search researcher blogs using stage-1 signals → researcher_blog_posts
    Stage 3 → Vendor advisories → vendor_advisory_posts
    Stage 4 → CVE/NVD/KEV sources → cve_findings
    Stage 5 → Correlate all stages, score → scored_posts (dashboard)
    """

    def __init__(self) -> None:
        self.extractor = SignalExtractor()
        self.scorer = ConfidenceScorer()
        self.correlator = Correlator()

    async def run(self, session: AsyncSession, request: PipelineRequest) -> PipelineResponse:
        repo = HuntRepository(session)
        started_at = datetime.now(timezone.utc)
        run = await repo.create_run(request.products)
        run_id = run.id

        stage_stats: dict[int, PipelineStageStats] = {}
        vuln_keywords = request.vulnerability_keywords or (
            VULNERABILITY_KEYWORDS + SEARCH_KEYWORDS
        )
        base_terms = self._build_query_terms(request.products)

        try:
            # ── STAGE 1: Researcher Social (X + LinkedIn) ──
            await repo.update_run(run_id, current_stage=STAGE_SOCIAL)
            social_terms = base_terms
            social_count = await self._run_stage_social(
                repo, run_id, social_terms, request.lookback_days,
                request.products, vuln_keywords,
            )
            stage_stats[STAGE_SOCIAL] = PipelineStageStats(
                stage=STAGE_SOCIAL,
                name="Researcher Social (X/LinkedIn)",
                sources_queried=len(SOCIAL_SOURCE_IDS),
                records_saved=social_count,
            )

            # Build expanded terms from stage 1 results
            social_posts = await repo.get_social_posts(run_id)
            expanded_terms = self._expand_terms_from_stage(social_posts, base_terms)

            # ── STAGE 2: Researcher Blogs ──
            await repo.update_run(run_id, current_stage=STAGE_BLOG)
            blog_count = await self._run_stage(
                repo, run_id, BLOG_SOURCE_IDS, expanded_terms,
                request.lookback_days, request.products, vuln_keywords,
                save_fn=repo.save_blog_post,
            )
            stage_stats[STAGE_BLOG] = PipelineStageStats(
                stage=STAGE_BLOG,
                name="Researcher Blogs",
                sources_queried=len(BLOG_SOURCE_IDS),
                records_saved=blog_count,
            )

            # ── STAGE 3: Vendor Advisories ──
            await repo.update_run(run_id, current_stage=STAGE_ADVISORY)
            advisory_count = await self._run_stage(
                repo, run_id, ADVISORY_SOURCE_IDS, expanded_terms,
                request.lookback_days, request.products, vuln_keywords,
                save_fn=repo.save_advisory_post,
            )
            stage_stats[STAGE_ADVISORY] = PipelineStageStats(
                stage=STAGE_ADVISORY,
                name="Vendor Advisories",
                sources_queried=len(ADVISORY_SOURCE_IDS),
                records_saved=advisory_count,
            )

            # ── STAGE 4: CVE / Vulnerability Sources ──
            await repo.update_run(run_id, current_stage=STAGE_CVE)
            cve_count = await self._run_stage(
                repo, run_id, CVE_SOURCE_IDS, expanded_terms,
                request.lookback_days, request.products, vuln_keywords,
                save_fn=repo.save_cve_finding,
            )
            stage_stats[STAGE_CVE] = PipelineStageStats(
                stage=STAGE_CVE,
                name="CVE & Vulnerability Sources",
                sources_queried=len(CVE_SOURCE_IDS),
                records_saved=cve_count,
            )

            # ── STAGE 5: Score & correlate all stages ──
            await repo.update_run(run_id, current_stage=STAGE_SCORE)
            posts = await self._run_stage_score(
                repo, run_id, request.products, vuln_keywords,
                request.min_confidence, request.include_low_confidence,
            )
            stage_stats[STAGE_SCORE] = PipelineStageStats(
                stage=STAGE_SCORE,
                name="Score & Correlate",
                sources_queried=0,
                records_saved=len(posts),
            )

            completed_at = datetime.now(timezone.utc)
            await repo.update_run(
                run_id,
                status="completed",
                current_stage=STAGE_SCORE,
                stage_stats={str(k): v.model_dump() for k, v in stage_stats.items()},
                completed_at=completed_at,
            )

            return PipelineResponse(
                hunt_id=run_id,
                query_products=request.products,
                status="completed",
                current_stage=STAGE_SCORE,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=round((completed_at - started_at).total_seconds(), 2),
                stages=list(stage_stats.values()),
                posts=posts,
                total_posts=len(posts),
            )

        except Exception as exc:
            logger.exception("Pipeline failed for run %s", run_id)
            await repo.update_run(
                run_id,
                status="failed",
                error_message=str(exc),
                completed_at=datetime.now(timezone.utc),
            )
            raise

    async def _run_stage_social(
        self,
        repo: HuntRepository,
        hunt_run_id: str,
        query_terms: list[str],
        lookback_days: int,
        products: list[str],
        vuln_keywords: list[str],
    ) -> int:
        saved = 0
        sources = get_enabled_sources(SOCIAL_SOURCE_IDS)

        for source in sources:
            collector = get_collector_for_source(source)
            try:
                result = await collector.collect(query_terms, lookback_days)
            except Exception as exc:
                logger.warning("Stage 1 source %s failed: %s", source.id, exc)
                continue

            if not result.success:
                logger.info("Stage 1 source %s skipped: %s", source.id, result.error)
                continue

            platform = "twitter" if source.id == "twitter" else "linkedin"
            for signal in result.signals:
                enrichment = self.extractor.enrich_signal(signal, products, vuln_keywords)
                if await repo.save_social_post(hunt_run_id, platform, signal, enrichment):
                    saved += 1

        return saved

    async def _run_stage(
        self,
        repo: HuntRepository,
        hunt_run_id: str,
        source_ids: list[str],
        query_terms: list[str],
        lookback_days: int,
        products: list[str],
        vuln_keywords: list[str],
        save_fn,
    ) -> int:
        saved = 0
        sources = get_enabled_sources(source_ids)

        tasks = [
            self._collect_from_source(source, query_terms, lookback_days)
            for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                logger.warning("Stage source %s error: %s", source.id, result)
                continue
            if not result.success:
                continue

            for signal in result.signals:
                enrichment = self.extractor.enrich_signal(signal, products, vuln_keywords)
                if not enrichment["matched_products"] and not enrichment["cves"]:
                    combined = f"{signal.title} {signal.content}".lower()
                    if not any(p.lower() in combined for p in products):
                        continue
                if await save_fn(hunt_run_id, signal, enrichment):
                    saved += 1

        return saved

    async def _run_stage_score(
        self,
        repo: HuntRepository,
        hunt_run_id: str,
        products: list[str],
        vuln_keywords: list[str],
        min_confidence: float,
        include_low_confidence: bool,
    ) -> list[ScoredPostResponse]:
        records = await repo.get_all_stage_records(hunt_run_id)
        findings: list[ThreatFinding] = []
        stage_map: dict[str, list[str]] = {}

        for stage, record in records:
            signal = self._record_to_signal(stage, record)
            enrichment = self.extractor.enrich_signal(signal, products, vuln_keywords)
            finding = self.scorer.score_signal(signal, enrichment, products)
            findings.append(finding)
            stage_map.setdefault(finding.id, []).append(stage)

        correlated = self.correlator.correlate(findings)
        min_conf = normalize_min_score(min_confidence, default=50.0)

        if include_low_confidence:
            final = correlated
        else:
            final = [f for f in correlated if f.confidence_score >= min_conf]

        posts: list[ScoredPostResponse] = []
        for finding in final:
            stages = list(dict.fromkeys(stage_map.get(finding.id, [])))
            await repo.save_scored_post(hunt_run_id, finding, stages)
            posts.append(scored_post_to_response(finding, hunt_run_id, stages))

        return posts

    def _record_to_signal(self, stage: str, record) -> RawSignal:
        category_map = {
            "social": SourceCategory.RESEARCHER_SOCIAL,
            "blog": SourceCategory.RESEARCHER_BLOG,
            "advisory": SourceCategory.VENDOR_ADVISORY,
            "cve": SourceCategory.VULNERABILITY,
        }
        cat = category_map.get(stage, SourceCategory.VULNERABILITY)
        method = CollectionMethod.RSS
        if stage == "social":
            method = CollectionMethod.HTML_SCRAPER

        return RawSignal(
            source_id=record.source_id,
            source_name=record.source_name,
            source_category=SchemaSourceCategory(cat.value),
            collection_method=method,
            title=record.title,
            url=record.url,
            content=record.content,
            published_at=record.published_at,
            author=getattr(record, "author", None),
            raw_metadata={
                "cves": json.loads(record.cves) if record.cves else [],
                "in_cisa_kev": getattr(record, "in_cisa_kev", False),
                "is_poc_repo": getattr(record, "has_poc", False),
            },
        )

    async def _collect_from_source(self, source, query_terms, lookback_days):
        collector = get_collector_for_source(source)
        return await collector.collect(query_terms, lookback_days)

    def _build_query_terms(self, products: list[str]) -> list[str]:
        terms = list(products)
        for product in products:
            terms.extend([
                f"{product} vulnerability",
                f"{product} exploit",
                f"{product} RCE",
                f"{product} authentication bypass",
                f"{product} PoC",
                f"{product} zero day",
            ])
        terms.extend(SEARCH_KEYWORDS)
        return list(dict.fromkeys(terms))

    def _expand_terms_from_stage(self, social_posts, base_terms: list[str]) -> list[str]:
        terms = list(base_terms)
        for post in social_posts:
            for field in ("cves", "matched_keywords", "matched_products", "vendors"):
                raw = getattr(post, field, "[]")
                try:
                    items = json.loads(raw) if raw else []
                except json.JSONDecodeError:
                    items = []
                terms.extend(items)
            words = post.title.split() + post.content.split()
            for word in words:
                if word.upper().startswith("CVE-"):
                    terms.append(word.upper())
        return list(dict.fromkeys(terms))


def scored_post_to_response(
    finding: ThreatFinding,
    hunt_run_id: str,
    stage_sources: list[str],
) -> ScoredPostResponse:
    return ScoredPostResponse(
        id=finding.id,
        hunt_run_id=hunt_run_id,
        title=finding.title,
        summary=finding.summary,
        url=finding.url,
        published_at=finding.published_at,
        vendors=finding.vendors,
        products=finding.products,
        cves=finding.cves,
        vulnerability_types=finding.vulnerability_types,
        threat_indicators=finding.threat_indicators,
        has_poc=finding.has_poc,
        active_exploitation=finding.active_exploitation,
        in_cisa_kev=finding.in_cisa_kev,
        is_vendor_advisory=finding.is_vendor_advisory,
        confidence_score=finding.confidence_score,
        source_trust_score=finding.source_trust_score,
        recency_score=finding.recency_score,
        keyword_match_score=finding.keyword_match_score,
        sources=finding.sources,
        source_categories=[c.value for c in finding.source_categories],
        stage_sources=stage_sources,
        correlated_count=finding.correlated_count,
        matched_keywords=finding.matched_keywords,
        matched_products=finding.matched_products,
    )


def db_post_to_response(post) -> ScoredPostResponse:
    return ScoredPostResponse(
        id=post.id,
        hunt_run_id=post.hunt_run_id,
        title=post.title,
        summary=post.summary,
        url=post.url,
        published_at=post.published_at,
        vendors=json.loads(post.vendors),
        products=json.loads(post.products),
        cves=json.loads(post.cves),
        vulnerability_types=json.loads(post.vulnerability_types),
        threat_indicators=json.loads(post.threat_indicators),
        has_poc=post.has_poc,
        active_exploitation=post.active_exploitation,
        in_cisa_kev=post.in_cisa_kev,
        is_vendor_advisory=post.is_vendor_advisory,
        confidence_score=post.confidence_score,
        risk_level=getattr(post, "risk_level", "LOW") or "LOW",
        score_breakdown=json.loads(getattr(post, "score_breakdown", None) or "{}"),
        score_reason=getattr(post, "score_reason", "") or "",
        source_trust_score=post.source_trust_score,
        recency_score=post.recency_score,
        keyword_match_score=post.keyword_match_score,
        sources=json.loads(post.sources),
        source_categories=json.loads(post.source_categories),
        stage_sources=json.loads(post.stage_sources),
        correlated_count=post.correlated_count,
        matched_keywords=json.loads(post.matched_keywords),
        matched_products=json.loads(post.matched_products),
        created_at=post.created_at,
    )
