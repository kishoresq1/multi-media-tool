import re
from datetime import datetime

from app.config.sources import SOURCE_REGISTRY
from app.services.threat_scorer import ThreatScorer

_RANSOMWARE_RE = re.compile(
    r"\b(ransomware|ransom|extortion|data leak site|lockbit|clop|blackcat|play ransomware)\b",
    re.I,
)
_BREACH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(data breach|breached|leaked records|stolen data)\b", re.I), "data_breach"),
    (re.compile(r"\b(cyberattack|cyber attack|hacked)\b", re.I), "cyberattack"),
]


class BreachScorer:
    """SAINT threat score for company breach news (0-100)."""

    def __init__(self) -> None:
        self._scorer = ThreatScorer()

    def score(
        self,
        title: str,
        content: str,
        source_id: str,
        published_at: datetime | None,
    ) -> dict:
        source = SOURCE_REGISTRY.get(source_id)
        source_name = source.name if source else source_id
        scores = self._scorer.score(
            title=title,
            content=content,
            source_id=source_id,
            source_name=source_name,
            published_at=published_at,
        )
        combined = f"{title} {content}"
        scores["is_ransomware"] = bool(_RANSOMWARE_RE.search(combined))
        scores["breach_type"] = self._detect_breach_type(combined, scores["is_ransomware"])
        scores["affected_company"] = self._guess_company(title, source_id)
        return scores

    def _detect_breach_type(self, text: str, is_ransomware: bool) -> str | None:
        if is_ransomware:
            return "ransomware"
        for pattern, label in _BREACH_PATTERNS:
            if pattern.search(text):
                return label
        if re.search(r"\bbreach\b", text, re.I):
            return "data_breach"
        return None

    def _guess_company(self, title: str, source_id: str) -> str | None:
        if source_id == "ransomware_live":
            # Titles often: "Company Name — GroupName"
            parts = re.split(r"\s[—–-]\s", title, maxsplit=1)
            if parts and len(parts[0].strip()) > 2:
                return parts[0].strip()[:200]
        return None
