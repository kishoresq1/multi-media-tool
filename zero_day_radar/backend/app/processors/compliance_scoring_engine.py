"""
SAINT Compliance Scoring Engine.

Calculates a compliance confidence score from 0-100 for a compliance finding or cluster.
Vendor/product/framework matching is assumed complete — this module only scores.
"""

from app.config.compliance_scoring import (
    BONUS_CONTROLS_IMPACTED,
    BONUS_DEADLINE,
    BONUS_EFFECTIVE_DATE,
    BONUS_FRAMEWORK_IDENTIFIED,
    BONUS_FRAMEWORK_UPDATE,
    BONUS_NEW_REQUIREMENT,
    BONUS_THREE_PLUS_SOURCES,
    BONUS_TWO_SOURCES,
    BONUS_VERSION_EXTRACTED,
    COMPLIANCE_SOURCE_SCORES,
    COMPLIANCE_SOURCE_TYPES,
    DEFAULT_SOURCE_SCORE,
    get_risk_level,
    get_source_score,
)


class ComplianceScoringEngine:
    """
    SAINT Compliance Scoring Engine.

    score = sum(source scores) + bonuses, capped at 100.
    """

    MAX_SCORE = 100

    def score_cluster(self, payload: dict) -> dict:
        """
        Score a compliance cluster from structured input.

        Expected input:
        {
            "organization_name": "",
            "framework_name": "",
            "sources": [{"source_id": "...", "source_type": "...", "source_name": "..."}],
            "framework_update": bool,
            "new_requirement": bool,
            "effective_date_present": bool,
            "deadline_present": bool,
            "controls_impacted": bool,
            "framework_identified": bool,
            "version_extracted": bool,
            "signal_count": int
        }
        """
        org = payload.get("organization_name") or ""
        framework = payload.get("framework_name") or ""
        sources = payload.get("sources") or []

        source_score, source_details = self._sum_source_scores(sources)
        bonus_score, bonus_details = self._calculate_bonuses(payload)

        raw = source_score + bonus_score
        confidence = min(self.MAX_SCORE, raw)
        risk_level = get_risk_level(confidence)
        reason = self._build_reason(sources, bonus_details, framework)

        return {
            "organization_name": org,
            "framework_name": framework,
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
        enrichment: dict,
    ) -> dict:
        """Score a single collected compliance signal using extraction enrichment."""
        payload = {
            "organization_name": enrichment.get("organization", ""),
            "framework_name": (enrichment.get("frameworks") or [""])[0] if enrichment.get("frameworks") else "",
            "sources": [{
                "source_id": source_id,
                "source_type": COMPLIANCE_SOURCE_TYPES.get(source_id, "Compliance"),
                "source_name": source_name,
            }],
            "framework_update": bool(enrichment.get("is_framework_update")),
            "new_requirement": bool(enrichment.get("is_new_requirement")),
            "effective_date_present": bool(enrichment.get("effective_dates")),
            "deadline_present": bool(enrichment.get("compliance_deadlines")),
            "controls_impacted": bool(enrichment.get("impacted_controls")),
            "framework_identified": bool(enrichment.get("frameworks")),
            "version_extracted": bool(enrichment.get("framework_versions")),
            "signal_count": 1,
        }
        return self.score_cluster(payload)

    def _sum_source_scores(self, sources: list[dict]) -> tuple[int, list[dict]]:
        seen: set[str] = set()
        total = 0
        details: list[dict] = []

        for src in sources:
            sid = src.get("source_id") or src.get("source_name", "")
            key = sid.lower()
            if key in seen:
                continue
            seen.add(key)

            points = get_source_score(sid)
            if sid not in COMPLIANCE_SOURCE_SCORES and src.get("source_name"):
                for known_id, pts in COMPLIANCE_SOURCE_SCORES.items():
                    if known_id in sid or sid in known_id:
                        points = pts
                        sid = known_id
                        break

            total += points
            details.append({
                "source_id": sid,
                "source_name": src.get("source_name", sid),
                "source_type": src.get("source_type") or COMPLIANCE_SOURCE_TYPES.get(sid, "Compliance"),
                "points": points,
            })

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

        if payload.get("framework_update"):
            bonus += BONUS_FRAMEWORK_UPDATE
            details.append(f"Framework update (+{BONUS_FRAMEWORK_UPDATE})")
        if payload.get("new_requirement"):
            bonus += BONUS_NEW_REQUIREMENT
            details.append(f"New requirement (+{BONUS_NEW_REQUIREMENT})")
        if payload.get("effective_date_present"):
            bonus += BONUS_EFFECTIVE_DATE
            details.append(f"Effective date identified (+{BONUS_EFFECTIVE_DATE})")
        if payload.get("deadline_present"):
            bonus += BONUS_DEADLINE
            details.append(f"Compliance deadline identified (+{BONUS_DEADLINE})")
        if payload.get("controls_impacted"):
            bonus += BONUS_CONTROLS_IMPACTED
            details.append(f"Impacted controls identified (+{BONUS_CONTROLS_IMPACTED})")
        if payload.get("framework_identified"):
            bonus += BONUS_FRAMEWORK_IDENTIFIED
            details.append(f"Framework identified (+{BONUS_FRAMEWORK_IDENTIFIED})")
        if payload.get("version_extracted"):
            bonus += BONUS_VERSION_EXTRACTED
            details.append(f"Version number extracted (+{BONUS_VERSION_EXTRACTED})")

        return bonus, details

    def _build_reason(
        self,
        sources: list[dict],
        bonus_details: list[str],
        framework: str,
    ) -> str:
        if not sources and not bonus_details:
            return "Insufficient compliance signal data."

        source_names = [s.get("source_name") or s.get("source_id", "Unknown") for s in sources[:3]]
        source_part = ", ".join(source_names)

        parts: list[str] = []
        if source_part:
            parts.append(f"Reported by {source_part}")

        if framework:
            parts.append(f"framework {framework}")

        high_value_bonuses = [
            d for d in bonus_details
            if "New requirement" in d or "Framework update" in d or "deadline" in d.lower()
        ]
        if high_value_bonuses:
            parts.append(high_value_bonuses[0].split(" (+")[0].lower())

        if len(parts) == 1 and bonus_details:
            return f"{parts[0]}. {bonus_details[0].split(' (+')[0]}."

        return ". ".join(parts) + "." if parts else "Compliance update detected from trusted source."
