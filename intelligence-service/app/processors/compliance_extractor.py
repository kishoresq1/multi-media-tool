import re

from app.config.compliance_keywords import FRAMEWORK_KEYWORDS

# Normalize framework aliases for extraction
FRAMEWORK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ISO 27001", re.compile(r"ISO[\s/]*27001", re.I)),
    ("ISO 27701", re.compile(r"ISO[\s/]*27701", re.I)),
    ("ISO 22301", re.compile(r"ISO[\s/]*22301", re.I)),
    ("ISO 42001", re.compile(r"ISO[\s/]*42001", re.I)),
    ("PCI DSS", re.compile(r"PCI[\s-]*DSS", re.I)),
    ("SOC 2", re.compile(r"SOC[\s-]*2", re.I)),
    ("NIST CSF", re.compile(r"NIST[\s-]*CSF|Cybersecurity Framework", re.I)),
    ("NIST 800-53", re.compile(r"NIST[\s-]*800-53|SP[\s-]*800-53", re.I)),
    ("NIST AI RMF", re.compile(r"NIST[\s-]*AI[\s-]*RMF|AI Risk Management Framework", re.I)),
    ("CIS Controls", re.compile(r"CIS[\s-]*Controls?", re.I)),
    ("CSA CCM", re.compile(r"CSA[\s-]*CCM|Cloud Controls Matrix", re.I)),
    ("CMMC", re.compile(r"\bCMMC\b", re.I)),
    ("HIPAA", re.compile(r"\bHIPAA\b", re.I)),
    ("GDPR", re.compile(r"\bGDPR\b|General Data Protection Regulation", re.I)),
    ("NIS2", re.compile(r"\bNIS2\b|NIS 2", re.I)),
    ("DORA", re.compile(r"\bDORA\b|Digital Operational Resilience Act", re.I)),
    ("EU AI Act", re.compile(r"EU[\s-]*AI[\s-]*Act|Artificial Intelligence Act", re.I)),
]

VERSION_PATTERN = re.compile(
    r"(?:version|v\.?|rev\.?)\s*(\d+(?:\.\d+){0,2})|"
    r"(\d+\.\d+(?:\.\d+)?)\s*(?:update|revision|release)",
    re.I,
)

DATE_PATTERN = re.compile(
    r"(?:effective|mandatory|compliance|deadline|by)\s*(?:date|on|by)?\s*"
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})",
    re.I,
)

DEADLINE_PATTERN = re.compile(
    r"(?:deadline|must comply by|compliance deadline|mandatory by|required by)\s*"
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})",
    re.I,
)

CONTROL_PATTERN = re.compile(
    r"(?:control[s]?\s*(?:\d+[\.\-]\d+|[A-Z]{2}[\-\.]?\d+)|"
    r"CIS Control \d+|AC-\d+|SC-\d+|AU-\d+|CM-\d+|IA-\d+|"
    r"CC\d+\.\d+|Requirement \d+\.\d+)",
    re.I,
)

NEW_REQUIREMENT_PATTERN = re.compile(
    r"new requirement|mandatory requirement|must implement|shall comply|"
    r"new obligation|required control",
    re.I,
)

FRAMEWORK_UPDATE_PATTERN = re.compile(
    r"framework update|updated framework|new version|revision|"
    r"control update|certification update",
    re.I,
)


class ComplianceExtractor:
    """Extract compliance-specific intelligence from text."""

    def extract_frameworks(self, text: str) -> list[str]:
        found: list[str] = []
        for name, pattern in FRAMEWORK_PATTERNS:
            if pattern.search(text):
                found.append(name)
        for kw in FRAMEWORK_KEYWORDS:
            if kw.lower() in text.lower() and kw not in found:
                found.append(kw)
        return list(dict.fromkeys(found))

    def extract_versions(self, text: str) -> list[str]:
        versions: list[str] = []
        for match in VERSION_PATTERN.finditer(text):
            val = match.group(1) or match.group(2)
            if val:
                versions.append(val)
        return list(dict.fromkeys(versions))[:10]

    def extract_effective_dates(self, text: str) -> list[str]:
        dates: list[str] = []
        for match in DATE_PATTERN.finditer(text):
            if match.group(1):
                dates.append(match.group(1).strip())
        return list(dict.fromkeys(dates))[:5]

    def extract_deadlines(self, text: str) -> list[str]:
        deadlines: list[str] = []
        for match in DEADLINE_PATTERN.finditer(text):
            if match.group(1):
                deadlines.append(match.group(1).strip())
        return list(dict.fromkeys(deadlines))[:5]

    def extract_impacted_controls(self, text: str) -> list[str]:
        controls = [m.group(0).strip() for m in CONTROL_PATTERN.finditer(text)]
        return list(dict.fromkeys(controls))[:15]

    def is_new_requirement(self, text: str) -> bool:
        return bool(NEW_REQUIREMENT_PATTERN.search(text))

    def is_framework_update(self, text: str) -> bool:
        return bool(FRAMEWORK_UPDATE_PATTERN.search(text))

    def enrich(self, title: str, content: str) -> dict:
        combined = f"{title} {content}"
        return {
            "frameworks": self.extract_frameworks(combined),
            "framework_versions": self.extract_versions(combined),
            "effective_dates": self.extract_effective_dates(combined),
            "compliance_deadlines": self.extract_deadlines(combined),
            "impacted_controls": self.extract_impacted_controls(combined),
            "is_new_requirement": self.is_new_requirement(combined),
            "is_framework_update": self.is_framework_update(combined),
        }
