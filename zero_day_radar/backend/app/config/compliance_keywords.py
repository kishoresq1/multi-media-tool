# =============================================================================
# COMPLIANCE KEYWORD PRIORITY
# -----------------------------------------------------------------------------
# 1. PRIMARY  → COMPLIANCE_SEARCH_KEYWORDS — used FIRST for scraper/API search
# 2. FALLBACK → privacy + audit + AI governance + framework keywords
# =============================================================================

COMPLIANCE_SEARCH_KEYWORDS: list[str] = [
    "compliance update",
    "new requirement",
    "framework update",
    "control update",
    "audit requirement",
    "audit guidance",
    "evidence requirement",
    "certification update",
    "compliance deadline",
    "mandatory requirement",
    "effective date",
]

PRIVACY_KEYWORDS: list[str] = [
    "GDPR",
    "privacy regulation",
    "data protection",
    "consent requirement",
    "cross-border transfer",
    "DPIA",
    "privacy impact assessment",
    "cookie compliance",
]

AUDIT_KEYWORDS: list[str] = [
    "audit finding",
    "audit observation",
    "non-compliance",
    "control deficiency",
    "gap assessment",
    "remediation plan",
]

AI_GOVERNANCE_KEYWORDS: list[str] = [
    "AI governance",
    "AI compliance",
    "EU AI Act",
    "ISO 42001",
    "NIST AI RMF",
    "responsible AI",
]

FRAMEWORK_KEYWORDS: list[str] = [
    "ISO 27001",
    "ISO 27701",
    "ISO 22301",
    "ISO 42001",
    "PCI DSS",
    "SOC 2",
    "NIST CSF",
    "NIST 800-53",
    "NIST AI RMF",
    "CIS Controls",
    "CSA CCM",
    "CMMC",
    "HIPAA",
    "GDPR",
    "NIS2",
    "DORA",
]

COMPLIANCE_FALLBACK_KEYWORDS: list[str] = list(dict.fromkeys(
    PRIVACY_KEYWORDS + AUDIT_KEYWORDS + AI_GOVERNANCE_KEYWORDS + FRAMEWORK_KEYWORDS
))
