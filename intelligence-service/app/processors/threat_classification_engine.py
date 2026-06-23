"""
SAINT Cyber Threat Classification Engine.

Classifies intelligence content as PRODUCT_VULNERABILITY, COMPANY_BREACH, or UNKNOWN.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

CVE_PATTERN = re.compile(r"CVE-\d{4}-\d+", re.I)

PRODUCT_VULN_TERMS: list[tuple[str, int]] = [
    (r"\bvulnerabilit(?:y|ies)\b", 12),
    (r"\bsecurity flaw\b", 12),
    (r"\bsecurity advis(?:ory|ories)\b", 14),
    (r"\bvendor advis(?:ory|ories)\b", 14),
    (r"\bexploit\b", 10),
    (r"\bproof of concept\b", 12),
    (r"\bpoc\b", 6),
    (r"\bauthentication bypass\b", 14),
    (r"\bprivilege escalation\b", 12),
    (r"\bremote code execution\b", 14),
    (r"\brce\b", 8),
    (r"\bzero[- ]day\b", 14),
    (r"\b0day\b", 10),
    (r"\bpatch\b", 6),
    (r"\baffected versions?\b", 10),
    (r"\bproduct vulnerabilit", 14),
    (r"\bfirmware\b", 6),
    (r"\bsoftware weakness\b", 12),
    (r"\bcvss\b", 8),
    (r"\bin the wild\b", 8),
]

COMPANY_BREACH_TERMS: list[tuple[str, int]] = [
    (r"\bdata breach\b", 16),
    (r"\bdata leak\b", 14),
    (r"\bcompany hacked\b", 16),
    (r"\bcompany breached\b", 16),
    (r"\bhas been (?:hacked|breached|compromised)\b", 14),
    (r"\bhit by ransomware\b", 16),
    (r"\bransomware (?:attack|incident|victim)\b", 14),
    (r"\bcredential(?:s)? (?:exposed|leaked|stolen)\b", 14),
    (r"\bcustomer data\b", 12),
    (r"\bunauthorized access\b", 12),
    (r"\brepository leak\b", 12),
    (r"\bgithub (?:leak|exposure|exposed)\b", 12),
    (r"\bcloud (?:storage )?exposure\b", 12),
    (r"\bsensitive data leak\b", 14),
    (r"\bcompromised\b", 8),
    (r"\bextortion\b", 8),
    (r"\bleaked database\b", 12),
    (r"\bstolen data\b", 10),
    (r"\bexposed (?:aws|api) (?:keys?|credentials?)\b", 12),
]

# Tables that strongly imply incident type
TABLE_TYPE_HINTS: dict[str, tuple[str, int]] = {
    "vulnerability_intel": ("PRODUCT_VULNERABILITY", 25),
    "vendor_advisory_intel": ("PRODUCT_VULNERABILITY", 22),
    "company_breach_intel": ("COMPANY_BREACH", 28),
}

COMPANY_NAME_PATTERNS = [
    re.compile(
        r"^([A-Z][A-Za-z0-9&.\- ]{1,50}?"
        r"(?:\s+(?:Corp|Corporation|Inc|LLC|Ltd|Bank|Hospital|University|Manufacturing))?)"
        r"\s+(?:hit by|GitHub|data breach|ransomware)",
        re.I,
    ),
    re.compile(r"^([A-Z][A-Za-z0-9&.\- ]{2,60}?)\s+(?:hit by|suffers?|reports?|discloses?|confirms?)\s", re.I),
    re.compile(r"^([A-Z][A-Za-z0-9&.\- ]{2,50}?)\s+(?:data breach|ransomware)", re.I),
    re.compile(r"([A-Z][A-Za-z0-9&.\- ]{1,40}?\s+(?:Corp|Corporation|Inc|LLC|Ltd|Bank|Hospital|University))\b"),
]

PRODUCT_IN_TITLE = re.compile(
    r"\b([A-Z][A-Za-z0-9.\-]+(?:\s+[A-Z][A-Za-z0-9.\-]+){0,3})\s+"
    r"(?:vulnerabilit|authentication bypass|remote code execution|rce|security flaw|zero[- ]day)",
    re.I,
)


@dataclass
class ClassificationResult:
    incident_type: str
    classification_confidence: int
    company_name: str
    vendor_name: str
    product_name: str
    cve: str
    incident_title: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


class ThreatClassificationEngine:
    """Rule-based SAINT incident type classifier with entity extraction."""

    def classify(
        self,
        title: str,
        content: str = "",
        *,
        source_table: str | None = None,
        vendor_hint: str | None = None,
        product_hint: str | None = None,
        company_hint: str | None = None,
        cves: list[str] | None = None,
        is_ransomware: bool = False,
    ) -> ClassificationResult:
        text = f"{title} {content}".strip()
        lower = text.lower()

        vuln_score = 0
        breach_score = 0
        vuln_hits: list[str] = []
        breach_hits: list[str] = []

        cve = ""
        if cves:
            cve = cves[0].upper()
            vuln_score += 30
            vuln_hits.append(cve)
        else:
            m = CVE_PATTERN.search(text)
            if m:
                cve = m.group(0).upper()
                vuln_score += 30
                vuln_hits.append(cve)

        for pattern, weight in PRODUCT_VULN_TERMS:
            if re.search(pattern, lower, re.I):
                vuln_score += weight
                vuln_hits.append(pattern)

        for pattern, weight in COMPANY_BREACH_TERMS:
            if re.search(pattern, lower, re.I):
                breach_score += weight
                breach_hits.append(pattern)

        if is_ransomware:
            breach_score += 20
            breach_hits.append("ransomware_flag")

        if source_table and source_table in TABLE_TYPE_HINTS:
            hint_type, boost = TABLE_TYPE_HINTS[source_table]
            if hint_type == "PRODUCT_VULNERABILITY":
                vuln_score += boost
            else:
                breach_score += boost

        if vuln_score > breach_score and vuln_score >= 15:
            incident_type = "PRODUCT_VULNERABILITY"
            confidence = min(99, 50 + vuln_score - breach_score // 2)
            reason = "Content describes a software or product security vulnerability."
        elif breach_score > vuln_score and breach_score >= 12:
            incident_type = "COMPANY_BREACH"
            confidence = min(99, 50 + breach_score - vuln_score // 2)
            reason = "Content describes a compromise or data exposure affecting an organization."
        elif vuln_score >= 12 and breach_score >= 12:
            incident_type = "COMPANY_BREACH" if breach_score >= vuln_score else "PRODUCT_VULNERABILITY"
            confidence = 55
            reason = "Mixed signals; classified by stronger keyword match."
        else:
            incident_type = "UNKNOWN"
            confidence = max(20, min(vuln_score, breach_score, 40))
            reason = "Insufficient indicators for product vulnerability or company breach."

        company_name = (company_hint or "").strip()
        vendor_name = (vendor_hint or "").strip()
        product_name = (product_hint or "").strip()

        if not company_name and incident_type == "COMPANY_BREACH":
            company_name = self._extract_company_name(title) or company_name

        if not vendor_name and incident_type == "PRODUCT_VULNERABILITY":
            vendor_name = self._extract_vendor_from_title(title, product_name)

        if not product_name and incident_type == "PRODUCT_VULNERABILITY":
            product_name = self._extract_product_name(title, vendor_name)

        if incident_type == "COMPANY_BREACH" and company_name and not vendor_name:
            vendor_name = ""

        incident_title = title.strip()[:300] if title else ""

        return ClassificationResult(
            incident_type=incident_type,
            classification_confidence=confidence,
            company_name=company_name[:150],
            vendor_name=vendor_name[:150],
            product_name=product_name[:150],
            cve=cve,
            incident_title=incident_title,
            reason=reason,
        )

    def _extract_company_name(self, title: str) -> str:
        for pat in COMPANY_NAME_PATTERNS:
            m = pat.search(title)
            if m:
                return m.group(1).strip()
        if " — " in title:
            left = title.split(" — ", 1)[0].strip()
            if 3 < len(left) < 80:
                return left
        return ""

    def _extract_vendor_from_title(self, title: str, product: str) -> str:
        if product:
            parts = product.split()
            if parts:
                return parts[0]
        m = PRODUCT_IN_TITLE.search(title)
        if m:
            return m.group(1).split()[0]
        words = title.split()
        if words and words[0][0].isupper():
            return words[0]
        return ""

    def _extract_product_name(self, title: str, vendor: str) -> str:
        m = PRODUCT_IN_TITLE.search(title)
        if m:
            return m.group(1).strip()
        if vendor:
            rest = title
            if vendor in title:
                idx = title.lower().find(vendor.lower())
                rest = title[idx + len(vendor):].strip()
            for term in ("authentication bypass", "remote code execution", "vulnerability", "zero-day", "zero day"):
                if term in rest.lower():
                    return rest.split(term)[0].strip()[:80]
        return ""
