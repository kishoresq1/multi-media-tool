import hashlib
import re
from datetime import datetime

from app.models.schemas import RawSignal, ThreatFinding
from app.processors.threat_scoring_engine import ThreatScoringEngine


class Correlator:
    """Correlate and deduplicate signals into unified findings."""

    def __init__(self) -> None:
        self.engine = ThreatScoringEngine()

    def correlate(
        self,
        findings: list[ThreatFinding],
    ) -> list[ThreatFinding]:
        if not findings:
            return []

        groups: dict[str, list[ThreatFinding]] = {}

        for finding in findings:
            key = self._correlation_key(finding)
            groups.setdefault(key, []).append(finding)

        merged: list[ThreatFinding] = []
        for _key, group in groups.items():
            if len(group) == 1:
                merged.append(group[0])
            else:
                merged.append(self._merge_group(group))

        merged.sort(
            key=lambda f: (f.confidence_score, f.published_at or datetime.min),
            reverse=True,
        )
        return merged

    def _correlation_key(self, finding: ThreatFinding) -> str:
        if finding.cves:
            return f"cve:{finding.cves[0].upper()}"

        normalized_title = re.sub(r"[^a-z0-9]", "", finding.title.lower())[:80]
        if normalized_title:
            return f"title:{normalized_title}"

        if finding.url:
            return f"url:{finding.url}"

        return f"id:{finding.id}"

    def _merge_group(self, group: list[ThreatFinding]) -> ThreatFinding:
        primary = max(group, key=lambda f: f.confidence_score)
        all_sources = list({s for f in group for s in f.sources})
        all_cves = list({c for f in group for c in f.cves})
        all_vendors = list({v for f in group for v in f.vendors})
        all_products = list({p for f in group for p in f.products})
        all_vuln_types = list({v for f in group for v in f.vulnerability_types})
        all_threat = list({t for f in group for t in f.threat_indicators})
        all_keywords = list({k for f in group for k in f.matched_keywords})
        all_categories = list({c for f in group for c in f.source_categories})
        all_methods = list({m for f in group for m in f.collection_methods})

        saint = self.engine.score_cluster({
            "vendor_name": all_vendors[0] if all_vendors else "",
            "product_name": all_products[0] if all_products else "",
            "sources": [{"source_name": name} for name in all_sources],
            "cve_present": bool(all_cves),
            "poc_available": any(f.has_poc for f in group),
            "actively_exploited": any(f.active_exploitation or f.in_cisa_kev for f in group),
            "signal_count": len(group),
        })
        breakdown = saint["score_breakdown"]

        return ThreatFinding(
            id=primary.id,
            title=primary.title,
            url=primary.url,
            summary=primary.summary,
            published_at=primary.published_at,
            vendors=all_vendors,
            products=all_products,
            cves=all_cves,
            vulnerability_types=all_vuln_types,
            threat_indicators=all_threat,
            has_poc=any(f.has_poc for f in group),
            active_exploitation=any(f.active_exploitation for f in group),
            in_cisa_kev=any(f.in_cisa_kev for f in group),
            is_vendor_advisory=any(f.is_vendor_advisory for f in group),
            confidence_score=float(saint["confidence_score"]),
            risk_level=saint["risk_level"],
            score_breakdown=breakdown,
            score_reason=saint["reason"],
            source_trust_score=float(breakdown["source_score"]),
            recency_score=max(f.recency_score for f in group),
            keyword_match_score=float(breakdown["bonus_score"]),
            sources=all_sources,
            source_categories=all_categories,
            collection_methods=all_methods,
            correlated_count=len(group),
            is_duplicate=len(group) > 1,
            matched_keywords=all_keywords,
            matched_products=all_products,
        )

    def is_repost(self, signal: RawSignal, seen_content_hashes: set[str]) -> bool:
        content_hash = hashlib.md5(
            f"{signal.title}{signal.url}".lower().encode()
        ).hexdigest()
        if content_hash in seen_content_hashes:
            return True
        seen_content_hashes.add(content_hash)
        return False
