import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.collectors.registry import get_collector_for_source
from app.config.keywords import SEARCH_KEYWORDS, VULNERABILITY_KEYWORDS
from app.services.score_fields import normalize_min_score
from app.config.sources import get_enabled_sources
from app.models.schemas import HuntRequest, HuntResponse, HuntStats, ThreatFinding
from app.processors.correlator import Correlator
from app.processors.extractor import SignalExtractor
from app.processors.scorer import ConfidenceScorer

logger = logging.getLogger(__name__)


class ThreatHunter:
    """
    SAINT Threat Intelligence Hunter — orchestrates the full pipeline:

    STEP 1: Collect signals from all configured sources
    STEP 2: Extract vendors, CVEs, PoC flags, exploitation indicators
    STEP 3: Score each signal for confidence
    STEP 4: Correlate duplicates and reposts
    STEP 5: Return high-confidence findings as structured JSON
    """

    def __init__(self) -> None:
        self.extractor = SignalExtractor()
        self.scorer = ConfidenceScorer()
        self.correlator = Correlator()

    async def hunt(self, request: HuntRequest) -> HuntResponse:
        started_at = datetime.now(timezone.utc)
        hunt_id = str(uuid.uuid4())

        sources = get_enabled_sources(request.source_ids)
        query_terms = self._build_query_terms(request.products)
        vuln_keywords = request.vulnerability_keywords or (
            VULNERABILITY_KEYWORDS + SEARCH_KEYWORDS
        )

        stats = HuntStats(sources_queried=len(sources))
        all_signals = []
        failed_sources: list[str] = []

        collection_tasks = [
            self._collect_from_source(source, query_terms, request.lookback_days)
            for source in sources
        ]
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)

        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                logger.error("Collector error for %s: %s", source.id, result)
                failed_sources.append(source.id)
                stats.sources_failed += 1
                continue

            if result.success:
                stats.sources_succeeded += 1
                all_signals.extend(result.signals)
            else:
                failed_sources.append(source.id)
                stats.sources_failed += 1
                if result.error:
                    logger.info("Source %s skipped: %s", source.id, result.error)

        stats.raw_signals_collected = len(all_signals)
        stats.failed_sources = failed_sources

        seen_hashes: set[str] = set()
        findings: list[ThreatFinding] = []

        for signal in all_signals:
            if self.correlator.is_repost(signal, seen_hashes):
                continue

            enrichment = self.extractor.enrich_signal(
                signal, request.products, vuln_keywords
            )

            if not enrichment["matched_products"] and not enrichment["cves"]:
                if not any(
                    term.lower() in f"{signal.title} {signal.content}".lower()
                    for term in request.products
                ):
                    continue

            finding = self.scorer.score_signal(signal, enrichment, request.products)
            findings.append(finding)

        stats.findings_before_dedup = len(findings)
        correlated = self.correlator.correlate(findings)
        stats.findings_after_dedup = len(correlated)

        min_conf = normalize_min_score(request.min_confidence, default=50.0)
        if request.include_low_confidence:
            final_findings = correlated
        else:
            final_findings = [f for f in correlated if f.confidence_score >= min_conf]

        stats.high_confidence_findings = len(final_findings)

        completed_at = datetime.now(timezone.utc)
        stats.duration_seconds = round(
            (completed_at - started_at).total_seconds(), 2
        )

        return HuntResponse(
            hunt_id=hunt_id,
            query_products=request.products,
            started_at=started_at,
            completed_at=completed_at,
            stats=stats,
            findings=final_findings,
        )

    async def _collect_from_source(self, source, query_terms, lookback_days):
        collector = get_collector_for_source(source)
        try:
            return await collector.collect(query_terms, lookback_days)
        except Exception as exc:
            logger.exception("Failed collecting from %s", source.id)
            from app.collectors.base import CollectorResult

            return CollectorResult(success=False, error=str(exc))

    def _build_query_terms(self, products: list[str]) -> list[str]:
        terms = list(products)
        for product in products:
            terms.extend(
                [
                    f"{product} vulnerability",
                    f"{product} exploit",
                    f"{product} RCE",
                    f"{product} authentication bypass",
                    f"{product} PoC",
                    f"{product} zero day",
                ]
            )
        terms.extend(SEARCH_KEYWORDS)
        return list(dict.fromkeys(terms))
