import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    CVEFinding,
    HuntRun,
    ResearcherBlogPost,
    ResearcherSocialPost,
    ScoredPost,
    VendorAdvisoryPost,
)
from app.models.schemas import RawSignal, ThreatFinding


def _json_dumps(data) -> str:
    return json.dumps(data, default=str)


def _json_loads(data: str | None, default=None):
    if not data:
        return default if default is not None else []
    return json.loads(data)


def content_hash(title: str, url: str | None = None) -> str:
    key = f"{title}:{url or ''}".lower().strip()
    return hashlib.sha256(key.encode()).hexdigest()


class HuntRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_run(self, products: list[str]) -> HuntRun:
        run = HuntRun(products=_json_dumps(products), status="running", current_stage=0)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def update_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        current_stage: int | None = None,
        stage_stats: dict | None = None,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        run = await self.session.get(HuntRun, run_id)
        if not run:
            return
        if status is not None:
            run.status = status
        if current_stage is not None:
            run.current_stage = current_stage
        if stage_stats is not None:
            run.stage_stats = _json_dumps(stage_stats)
        if error_message is not None:
            run.error_message = error_message
        if completed_at is not None:
            run.completed_at = completed_at
        await self.session.commit()

    async def get_run(self, run_id: str) -> HuntRun | None:
        return await self.session.get(HuntRun, run_id)

    async def list_runs(self, limit: int = 20) -> list[HuntRun]:
        result = await self.session.execute(
            select(HuntRun).order_by(HuntRun.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def save_social_post(
        self,
        hunt_run_id: str,
        platform: str,
        signal: RawSignal,
        enrichment: dict,
    ) -> bool:
        ch = content_hash(signal.title, signal.url)
        post = ResearcherSocialPost(
            hunt_run_id=hunt_run_id,
            platform=platform,
            source_id=signal.source_id,
            source_name=signal.source_name,
            title=signal.title,
            content=signal.content,
            url=signal.url,
            author=signal.author,
            published_at=signal.published_at,
            matched_keywords=_json_dumps(enrichment.get("matched_keywords", [])),
            matched_products=_json_dumps(enrichment.get("matched_products", [])),
            cves=_json_dumps(enrichment.get("cves", [])),
            vendors=_json_dumps(enrichment.get("vendors", [])),
            content_hash=ch,
        )
        try:
            self.session.add(post)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def save_blog_post(
        self, hunt_run_id: str, signal: RawSignal, enrichment: dict
    ) -> bool:
        ch = content_hash(signal.title, signal.url)
        post = ResearcherBlogPost(
            hunt_run_id=hunt_run_id,
            source_id=signal.source_id,
            source_name=signal.source_name,
            title=signal.title,
            content=signal.content,
            url=signal.url,
            author=signal.author,
            published_at=signal.published_at,
            matched_keywords=_json_dumps(enrichment.get("matched_keywords", [])),
            matched_products=_json_dumps(enrichment.get("matched_products", [])),
            cves=_json_dumps(enrichment.get("cves", [])),
            vendors=_json_dumps(enrichment.get("vendors", [])),
            content_hash=ch,
        )
        try:
            self.session.add(post)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def save_advisory_post(
        self, hunt_run_id: str, signal: RawSignal, enrichment: dict
    ) -> bool:
        ch = content_hash(signal.title, signal.url)
        post = VendorAdvisoryPost(
            hunt_run_id=hunt_run_id,
            source_id=signal.source_id,
            source_name=signal.source_name,
            title=signal.title,
            content=signal.content,
            url=signal.url,
            published_at=signal.published_at,
            matched_keywords=_json_dumps(enrichment.get("matched_keywords", [])),
            matched_products=_json_dumps(enrichment.get("matched_products", [])),
            cves=_json_dumps(enrichment.get("cves", [])),
            vendors=_json_dumps(enrichment.get("vendors", [])),
            content_hash=ch,
        )
        try:
            self.session.add(post)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def save_cve_finding(
        self, hunt_run_id: str, signal: RawSignal, enrichment: dict
    ) -> bool:
        ch = content_hash(signal.title, signal.url)
        metadata = signal.raw_metadata or {}
        finding = CVEFinding(
            hunt_run_id=hunt_run_id,
            source_id=signal.source_id,
            source_name=signal.source_name,
            title=signal.title,
            content=signal.content,
            url=signal.url,
            published_at=signal.published_at,
            cves=_json_dumps(enrichment.get("cves", [])),
            cvss_score=metadata.get("cvss_score"),
            in_cisa_kev=enrichment.get("in_cisa_kev", False),
            has_poc=enrichment.get("has_poc", False),
            matched_keywords=_json_dumps(enrichment.get("matched_keywords", [])),
            matched_products=_json_dumps(enrichment.get("matched_products", [])),
            vendors=_json_dumps(enrichment.get("vendors", [])),
            content_hash=ch,
        )
        try:
            self.session.add(finding)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

    async def save_scored_post(
        self, hunt_run_id: str, finding: ThreatFinding, stage_sources: list[str]
    ) -> None:
        post = ScoredPost(
            id=finding.id,
            hunt_run_id=hunt_run_id,
            title=finding.title,
            summary=finding.summary,
            url=finding.url,
            published_at=finding.published_at,
            vendors=_json_dumps(finding.vendors),
            products=_json_dumps(finding.products),
            cves=_json_dumps(finding.cves),
            vulnerability_types=_json_dumps(finding.vulnerability_types),
            threat_indicators=_json_dumps(finding.threat_indicators),
            has_poc=finding.has_poc,
            active_exploitation=finding.active_exploitation,
            in_cisa_kev=finding.in_cisa_kev,
            is_vendor_advisory=finding.is_vendor_advisory,
            confidence_score=finding.confidence_score,
            risk_level=finding.risk_level,
            score_breakdown=_json_dumps(finding.score_breakdown),
            score_reason=finding.score_reason,
            source_trust_score=finding.source_trust_score,
            recency_score=finding.recency_score,
            keyword_match_score=finding.keyword_match_score,
            sources=_json_dumps(finding.sources),
            source_categories=_json_dumps([c.value for c in finding.source_categories]),
            collection_methods=_json_dumps([m.value for m in finding.collection_methods]),
            stage_sources=_json_dumps(stage_sources),
            correlated_count=finding.correlated_count,
            matched_keywords=_json_dumps(finding.matched_keywords),
            matched_products=_json_dumps(finding.matched_products),
        )
        self.session.add(post)
        await self.session.commit()

    async def get_social_posts(self, hunt_run_id: str) -> list[ResearcherSocialPost]:
        result = await self.session.execute(
            select(ResearcherSocialPost).where(
                ResearcherSocialPost.hunt_run_id == hunt_run_id
            )
        )
        return list(result.scalars().all())

    async def get_all_stage_records(self, hunt_run_id: str) -> list[tuple[str, object]]:
        records: list[tuple[str, object]] = []
        for stage, model in [
            ("social", ResearcherSocialPost),
            ("blog", ResearcherBlogPost),
            ("advisory", VendorAdvisoryPost),
            ("cve", CVEFinding),
        ]:
            result = await self.session.execute(
                select(model).where(model.hunt_run_id == hunt_run_id)
            )
            for row in result.scalars().all():
                records.append((stage, row))
        return records

    async def get_scored_posts(
        self,
        hunt_run_id: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScoredPost]:
        query = select(ScoredPost).where(ScoredPost.confidence_score >= min_confidence)
        if hunt_run_id:
            query = query.where(ScoredPost.hunt_run_id == hunt_run_id)
        query = (
            query.order_by(ScoredPost.confidence_score.desc(), ScoredPost.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scored_post(self, post_id: str) -> ScoredPost | None:
        return await self.session.get(ScoredPost, post_id)
