import re

from app.config.keywords import (
    THREAT_ACTIVITY_KEYWORDS,
    VENDOR_KEYWORDS,
    VULNERABILITY_KEYWORDS,
)
from app.config.sources import SOURCE_REGISTRY
from app.models.schemas import RawSignal, SourceCategory

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)

POC_PATTERNS = [
    r"\bpoc\b",
    r"proof[\s-]of[\s-]concept",
    r"exploit[\s-]released",
    r"working[\s-]exploit",
    r"public[\s-]exploit",
    r"github\.com/.+/(exploit|poc|cve)",
]

ACTIVE_EXPLOITATION_PATTERNS = [
    r"actively[\s-]exploited",
    r"active[\s-]exploitation",
    r"in[\s-]the[\s-]wild",
    r"exploitation[\s-]detected",
    r"mass[\s-]scanning",
    r"internet[\s-]scanning",
    r"patch[\s-]immediately",
    r"exploit[\s-]chain",
]

VULN_TYPE_MAP: dict[str, list[str]] = {
    "authentication bypass": ["auth bypass", "login bypass", "authentication bypass"],
    "RCE": ["rce", "remote code execution", "arbitrary code execution"],
    "privilege escalation": ["privesc", "privilege escalation"],
    "SQL injection": ["sqli", "sql injection"],
    "XSS": ["xss", "cross site scripting"],
    "SSRF": ["ssrf", "server side request forgery"],
    "path traversal": ["path traversal", "directory traversal"],
    "command injection": ["command injection", "code injection"],
    "buffer overflow": ["buffer overflow", "memory corruption"],
    "deserialization": ["deserialization"],
    "zero day": ["zero day", "0day", "zero-day"],
}


class SignalExtractor:
    def extract_cves(self, text: str) -> list[str]:
        return list({m.upper() for m in CVE_PATTERN.findall(text)})

    def extract_vendors(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for vendor in VENDOR_KEYWORDS:
            if vendor.lower() in text_lower:
                found.append(vendor)
        return found

    def extract_vulnerability_types(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for vuln_type, patterns in VULN_TYPE_MAP.items():
            if any(p in text_lower for p in patterns):
                found.append(vuln_type)
        return found

    def extract_threat_indicators(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for kw in THREAT_ACTIVITY_KEYWORDS:
            if kw.lower() in text_lower:
                found.append(kw)
        return found

    def extract_matched_keywords(
        self,
        text: str,
        query_products: list[str],
        extra_keywords: list[str] | None = None,
    ) -> tuple[list[str], list[str]]:
        text_lower = text.lower()
        matched_products = [
            p for p in query_products if p.lower() in text_lower
        ]
        keywords = VULNERABILITY_KEYWORDS + (extra_keywords or [])
        matched_keywords = [kw for kw in keywords if kw.lower() in text_lower]
        return matched_products, matched_keywords

    def has_poc(self, text: str, metadata: dict | None = None) -> bool:
        if metadata and metadata.get("is_poc_repo"):
            return True
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in POC_PATTERNS)

    def has_active_exploitation(self, text: str, metadata: dict | None = None) -> bool:
        if metadata and metadata.get("cisa_kev"):
            return True
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in ACTIVE_EXPLOITATION_PATTERNS)

    def is_vendor_advisory(self, source_id: str) -> bool:
        source = SOURCE_REGISTRY.get(source_id)
        if not source:
            return False
        return source.category.value == SourceCategory.VENDOR_ADVISORY.value

    def is_in_cisa_kev(self, metadata: dict | None) -> bool:
        return bool(metadata and metadata.get("cisa_kev"))

    def enrich_signal(
        self,
        signal: RawSignal,
        query_products: list[str],
        extra_keywords: list[str] | None = None,
    ) -> dict:
        combined = f"{signal.title} {signal.content}"
        matched_products, matched_keywords = self.extract_matched_keywords(
            combined, query_products, extra_keywords
        )
        return {
            "cves": self.extract_cves(combined),
            "vendors": self.extract_vendors(combined),
            "products": matched_products,
            "vulnerability_types": self.extract_vulnerability_types(combined),
            "threat_indicators": self.extract_threat_indicators(combined),
            "has_poc": self.has_poc(combined, signal.raw_metadata),
            "active_exploitation": self.has_active_exploitation(
                combined, signal.raw_metadata
            ),
            "in_cisa_kev": self.is_in_cisa_kev(signal.raw_metadata),
            "is_vendor_advisory": self.is_vendor_advisory(signal.source_id),
            "matched_keywords": matched_keywords,
            "matched_products": matched_products,
        }
