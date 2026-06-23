"""
Unified intel pipeline:

1. Run all collection APIs (social, advisories, blogs, vulnerabilities, compliance)
2. Aggregate rows from all SQLite intel tables
3. Ollama LLM enrichment (vendor, product, version, summary)
4. SAINT threat + compliance scoring → single unified_intel row
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.threat_scoring import get_risk_level as get_threat_risk_level
from app.db.unified_repository import UnifiedIntelRepository
from app.models.schemas import UnifiedIntelResponse, UnifiedRunRequest, UnifiedRunResponse
from app.processors.compliance_scoring_engine import ComplianceScoringEngine
from app.processors.threat_classification_engine import ThreatClassificationEngine
from app.processors.threat_scoring_engine import ThreatScoringEngine
from app.services.score_fields import parse_score_breakdown
from app.services.unified.aggregator import UnifiedAggregator
from app.services.unified.normalizer import NormalizedRecord
from app.services.unified.ollama_client import OllamaClient
from app.worker.jobs import refresh_all

logger = logging.getLogger(__name__)


class UnifiedIntelService:
    def __init__(self) -> None:
        self.aggregator = UnifiedAggregator()
        self.ollama = OllamaClient()
        self.threat_engine = ThreatScoringEngine()
        self.compliance_engine = ComplianceScoringEngine()
        self.classifier = ThreatClassificationEngine()

    async def run_pipeline(
        self,
        session: AsyncSession,
        request: UnifiedRunRequest,
    ) -> UnifiedRunResponse:
        started_at = datetime.now(timezone.utc)
        collection_stats: dict[str, Any] = {}

        if request.run_collections:
            logger.info("Unified pipeline: running all collection APIs")
            collection_stats = await refresh_all(lookback_days=request.lookback_days)

        records = await self.aggregator.load_all_records(session)
        groups = self.aggregator.group_records(records)

        ollama_ok = request.use_llm and await self.ollama.is_available()
        repo = UnifiedIntelRepository(session)
        saved: list[UnifiedIntelResponse] = []

        if request.replace_existing:
            cleared = await repo.clear_all()
            logger.info("Cleared %d existing unified_intel rows", cleared)

        for key, group in groups.items():
            row = await self._build_unified_row(
                key, group, ollama_ok, request.min_confidence
            )
            if not row:
                continue
            db_row = await repo.upsert(row)
            if db_row:
                saved.append(unified_to_response(db_row))

        saved.sort(
            key=lambda r: (
                -(r.latest_date.timestamp() if r.latest_date else 0),
                r.confidence_score,
            ),
        )

        completed_at = datetime.now(timezone.utc)
        total_in_db = await repo.count(min_score=request.min_confidence)

        return UnifiedRunResponse(
            run_id=str(uuid.uuid4()),
            collections_ran=request.run_collections,
            collection_stats=collection_stats,
            source_records_loaded=len(records),
            clusters_processed=len(groups),
            items_saved=len(saved),
            total_in_database=total_in_db,
            ollama_used=ollama_ok,
            ollama_model=self.ollama.model if ollama_ok else None,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=round((completed_at - started_at).total_seconds(), 2),
            items=saved[: request.result_limit],
        )

    async def _build_unified_row(
        self,
        cluster_key: str,
        group: list[NormalizedRecord],
        ollama_ok: bool,
        min_score: float,
    ) -> dict[str, Any] | None:
        vendor_hint = next((r.vendor for r in group if r.vendor), "Unknown")
        product_hint = next((r.product for r in group if r.product), group[0].title[:80])

        llm_data: dict[str, Any] | None = None
        if ollama_ok:
            llm_input = [
                {
                    "table": r.table,
                    "source": r.source_name,
                    "title": r.title,
                    "content": r.content[:400],
                    "vendor": r.vendor,
                    "cves": r.cves,
                    "frameworks": r.frameworks,
                }
                for r in group[:10]
            ]
            llm_data = await self.ollama.enrich_cluster(vendor_hint, product_hint, llm_input)

        vendor_name = (llm_data or {}).get("vendor_name") or vendor_hint or "Unknown"
        product_name = (llm_data or {}).get("product_name") or product_hint or ""
        version_name = (llm_data or {}).get("version_name") or next(
            (r.version for r in group if r.version), None
        )

        all_cves = list(dict.fromkeys(cve for r in group for cve in r.cves))
        if llm_data and llm_data.get("primary_cve"):
            pcve = llm_data["primary_cve"]
            if pcve not in all_cves:
                all_cves.insert(0, pcve)

        all_frameworks = list(dict.fromkeys(fw for r in group for fw in r.frameworks))
        latest = self.aggregator.latest_date(group)
        title = self.aggregator.pick_title(group)

        threat_score, compliance_score, breakdown, reason = self._score_cluster(
            group, vendor_name, product_name, all_cves
        )
        confidence = min(100.0, max(threat_score, compliance_score))
        if threat_score > 0 and compliance_score > 0:
            confidence = min(100.0, round((threat_score * 0.6 + compliance_score * 0.4)))

        risk_level = get_threat_risk_level(int(confidence))

        if confidence < min_score:
            return None

        source_refs = [
            {"table": r.table, "id": r.record_id, "source_name": r.source_name, "domain": r.domain}
            for r in group
        ]

        summary = (llm_data or {}).get("summary") or group[0].content[:500] or title

        primary = max(group, key=lambda r: (r.confidence_score, r.published_at or datetime.min))
        company_hint = next((r.company for r in group if r.company), None)
        is_ransomware = any(r.is_ransomware for r in group)

        classification = self.classifier.classify(
            title,
            summary,
            source_table=primary.table,
            vendor_hint=vendor_name,
            product_hint=product_name,
            company_hint=company_hint,
            cves=all_cves,
            is_ransomware=is_ransomware,
        )

        resolved_company: str | None = company_hint
        if classification.incident_type == "COMPANY_BREACH":
            resolved_company = classification.company_name or company_hint
            product_name = ""
        elif classification.incident_type == "PRODUCT_VULNERABILITY":
            if classification.vendor_name:
                vendor_name = classification.vendor_name
            if classification.product_name:
                product_name = classification.product_name
            resolved_company = None

        if classification.incident_title:
            title = classification.incident_title

        breakdown["classification"] = classification.to_dict()

        if all_cves:
            final_key = f"cve:{all_cves[0].upper()}"
        elif classification.incident_type == "COMPANY_BREACH" and resolved_company:
            final_key = f"breach:{resolved_company.lower()[:60]}:{title[:40].lower()}"
        else:
            final_key = (
                f"{vendor_name.lower()[:60]}:"
                f"{(product_name or 'unknown').lower()[:60]}:"
                f"{(version_name or 'any').lower()[:30]}"
            )

        return {
            "id": str(uuid.uuid4()),
            "company_name": resolved_company,
            "vendor_name": vendor_name[:150],
            "product_name": (product_name or "")[:150],
            "version_name": (version_name[:100] if version_name else None),
            "latest_date": latest,
            "title": title,
            "summary": summary[:2000],
            "cves": json.dumps(all_cves if not classification.cve else list(dict.fromkeys([classification.cve] + all_cves))),
            "frameworks": json.dumps(all_frameworks),
            "threat_score": round(threat_score, 1),
            "compliance_score": round(compliance_score, 1),
            "confidence_score": round(confidence, 1),
            "risk_level": risk_level,
            "classification": classification.incident_type,
            "classification_confidence": float(classification.classification_confidence),
            "classification_reason": classification.reason,
            "score_breakdown": json.dumps(breakdown),
            "score_reason": reason,
            "source_count": len(group),
            "source_refs": json.dumps(source_refs),
            "llm_summary": summary if llm_data else None,
            "llm_model": (llm_data or {}).get("llm_model"),
            "llm_enriched": bool(llm_data),
            "cluster_key": final_key[:200],
        }

    def _score_cluster(
        self,
        group: list[NormalizedRecord],
        vendor_name: str,
        product_name: str,
        cves: list[str],
    ) -> tuple[float, float, dict, str]:
        threat_records = [r for r in group if r.domain == "threat"]
        compliance_records = [r for r in group if r.domain == "compliance"]

        threat_score = 0.0
        compliance_score = 0.0
        threat_breakdown: dict = {}
        compliance_breakdown: dict = {}
        reasons: list[str] = []

        if threat_records:
            threat_sources = [
                {"source_id": r.source_id, "source_name": r.source_name}
                for r in threat_records
            ]
            has_poc = any(r.has_poc for r in threat_records)
            active = any(r.active_exploitation or r.in_cisa_kev for r in threat_records)
            saint = self.threat_engine.score_cluster({
                "vendor_name": vendor_name,
                "product_name": product_name,
                "sources": threat_sources,
                "cve_present": bool(cves),
                "poc_available": has_poc,
                "actively_exploited": active,
                "signal_count": len(threat_records),
            })
            threat_score = float(saint["confidence_score"])
            threat_breakdown = saint["score_breakdown"]
            reasons.append(saint["reason"])

        if compliance_records:
            comp_sources = [
                {"source_id": r.source_id, "source_name": r.source_name}
                for r in compliance_records
            ]
            saint_c = self.compliance_engine.score_cluster({
                "organization_name": vendor_name,
                "framework_name": product_name,
                "sources": comp_sources,
                "framework_update": any(r.is_framework_update for r in compliance_records),
                "new_requirement": any(r.is_new_requirement for r in compliance_records),
                "framework_identified": bool(
                    next((r.frameworks for r in compliance_records if r.frameworks), [])
                ),
                "signal_count": len(compliance_records),
            })
            compliance_score = float(saint_c["confidence_score"])
            compliance_breakdown = saint_c["score_breakdown"]
            reasons.append(saint_c["reason"])

        breakdown = {
            "threat": threat_breakdown,
            "compliance": compliance_breakdown,
            "threat_score": threat_score,
            "compliance_score": compliance_score,
        }
        reason = " | ".join(r for r in reasons if r) or "Consolidated intelligence cluster."
        return threat_score, compliance_score, breakdown, reason


def unified_to_response(row) -> UnifiedIntelResponse:
    return UnifiedIntelResponse(
        id=row.id,
        company_name=getattr(row, "company_name", None),
        vendor_name=row.vendor_name,
        product_name=row.product_name,
        version_name=row.version_name,
        latest_date=row.latest_date,
        title=row.title,
        summary=row.summary,
        cves=json.loads(row.cves or "[]"),
        frameworks=json.loads(row.frameworks or "[]"),
        threat_score=row.threat_score,
        compliance_score=row.compliance_score,
        confidence_score=row.confidence_score,
        risk_level=row.risk_level,
        classification=row.classification,
        classification_confidence=getattr(row, "classification_confidence", 0.0) or 0.0,
        classification_reason=getattr(row, "classification_reason", None),
        score_breakdown=parse_score_breakdown(row.score_breakdown),
        score_reason=row.score_reason,
        source_count=row.source_count,
        source_refs=json.loads(row.source_refs or "[]"),
        llm_summary=row.llm_summary,
        llm_model=row.llm_model,
        llm_enriched=row.llm_enriched,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
