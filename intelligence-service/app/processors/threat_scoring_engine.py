"""
SAINT Threat Scoring Engine.

Calculates a threat confidence score from 0-100 for a vulnerability cluster.
Vendor/product matching is assumed complete — only scores.
"""

from app.config.threat_scoring import (
    BONUS_ACTIVE_EXPLOITATION,
    BONUS_CVE_PRESENT,
    BONUS_POC_AVAILABLE,
    BONUS_THREE_PLUS_SOURCES,
    BONUS_TWO_SOURCES,
    get_risk_level,
    get_source_score,
)


class ThreatScoringEngine:
    """
    SAINT Threat Scoring Engine.

    score = sum(source scores) + bonuses, capped at 100.
    """

    MAX_SCORE = 100

    def score_cluster(self, payload: dict) -> dict:
        """
        Score a threat cluster.

        Input:
        {
            "vendor_name": "",
            "product_name": "",
            "sources": [{"source_id": "", "source_type": "", "source_name": ""}],
            "cve_present": bool,
            "poc_available": bool,
            "actively_exploited": bool,
            "signal_count": int
        }
        """
        vendor = payload.get("vendor_name") or ""
        product = payload.get("product_name") or ""
        sources = payload.get("sources") or []

        source_score, source_details = self._sum_source_scores(sources)
        bonus_score, bonus_details = self._calculate_bonuses(payload)

        raw = source_score + bonus_score
        confidence = min(self.MAX_SCORE, raw)
        risk_level = get_risk_level(confidence)
        reason = self._build_reason(
            vendor, product, sources, bonus_details, payload
        )

        return {
            "vendor_name": vendor,
            "product_name": product,
            "confidence_score": confidence,
            "risk_level": risk_level,
            "score_breakdown": {
                "source_score": source_score,
                "bonus_score": bonus_score,
                "source_details": source_details,
                "bonus_details": bonus_details,
                "raw_total": raw,
            },
            "reason": reason,
        }

    def score_signal(
        self,
        source_id: str,
        source_name: str,
        source_type: str | None,
        enrichment: dict,
    ) -> dict:
        """Score a single collected threat signal."""
        payload = {
            "vendor_name": enrichment.get("vendor_name", ""),
            "product_name": enrichment.get("product_name", ""),
            "sources": [{
                "source_id": source_id,
                "source_type": source_type or "",
                "source_name": source_name,
            }],
            "cve_present": bool(enrichment.get("cve_present")),
            "poc_available": bool(enrichment.get("poc_available")),
            "actively_exploited": bool(enrichment.get("actively_exploited")),
            "signal_count": enrichment.get("signal_count", 1),
        }
        return self.score_cluster(payload)

    def _sum_source_scores(self, sources: list[dict]) -> tuple[int, list[dict]]:
        seen: set[str] = set()
        total = 0
        details: list[dict] = []

        for src in sources:
            sid = (src.get("source_id") or src.get("source_name") or "").lower().strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)

            points = get_source_score(
                source_id=src.get("source_id"),
                source_name=src.get("source_name"),
                source_type=src.get("source_type"),
            )
            details.append({
                "source_id": src.get("source_id") or sid,
                "source_name": src.get("source_name") or sid,
                "source_type": src.get("source_type") or "",
                "points": points,
            })
            total += points

        return total, details

    def _calculate_bonuses(self, payload: dict) -> tuple[int, list[str]]:
        bonus = 0
        details: list[str] = []

        signal_count = payload.get("signal_count") or len(payload.get("sources") or [])
        if signal_count >= 3:
            bonus += BONUS_THREE_PLUS_SOURCES
            details.append(f"{signal_count} independent sources (+{BONUS_THREE_PLUS_SOURCES})")
        elif signal_count >= 2:
            bonus += BONUS_TWO_SOURCES
            details.append(f"{signal_count} independent sources (+{BONUS_TWO_SOURCES})")

        if payload.get("poc_available"):
            bonus += BONUS_POC_AVAILABLE
            details.append(f"PoC available (+{BONUS_POC_AVAILABLE})")
        if payload.get("actively_exploited"):
            bonus += BONUS_ACTIVE_EXPLOITATION
            details.append(f"Active exploitation (+{BONUS_ACTIVE_EXPLOITATION})")
        if payload.get("cve_present"):
            bonus += BONUS_CVE_PRESENT
            details.append(f"CVE present (+{BONUS_CVE_PRESENT})")

        return bonus, details

    def _build_reason(
        self,
        vendor: str,
        product: str,
        sources: list[dict],
        bonus_details: list[str],
        payload: dict,
    ) -> str:
        has_kev = any(
            "cisa" in (s.get("source_name") or "").lower()
            or s.get("source_id") == "cisa_kev"
            for s in sources
        )
        has_advisory = any(
            "advisory" in (s.get("source_type") or "").lower()
            or (s.get("source_id") or "") in {
                "msrc", "fortinet_psirt", "cisco_advisories",
            }
            for s in sources
        )
        has_poc_source = any(
            sid in (s.get("source_id") or "")
            for s in sources
            for sid in ("github_poc", "exploit_db", "metasploit")
        )

        if (
            len(sources) >= 3
            and payload.get("poc_available")
            and (payload.get("actively_exploited") or has_kev)
        ):
            return (
                "Multiple trusted sources, public exploit available, and active "
                "exploitation confirmed by CISA KEV."
            )

        if has_advisory and payload.get("poc_available"):
            return "Official vendor advisory and public PoC are available."

        if has_kev:
            return "Active exploitation confirmed by CISA KEV catalog."

        source_names = [s.get("source_name") or s.get("source_id", "") for s in sources[:3]]
        if source_names:
            label = f"{vendor} {product}".strip() or "Threat"
            return f"{label} signal from {', '.join(source_names)}."

        if bonus_details:
            return bonus_details[0].split(" (+")[0] + "."

        return "Threat intelligence signal detected."
