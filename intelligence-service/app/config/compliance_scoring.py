"""
SAINT Compliance Scoring Engine — source point values (0-100 scale).

Mirrors the SAINT Threat Scoring Engine structure for compliance intelligence.
"""

# Per-source scores keyed by source_id
COMPLIANCE_SOURCE_SCORES: dict[str, int] = {
    # Tier 1 — regulators & standards bodies (highest priority)
    "nist_compliance": 25,
    "iso_compliance": 25,
    "pci_ssc": 25,
    "enisa": 22,
    "edpb": 22,
    "cisa_guidance": 22,
    "eu_ai_act": 25,
    "iapp": 18,
    # Regulatory
    "ec_digital": 20,
    "uk_ncsc": 20,
    "hhs_ocr_hipaa": 20,
    "sec_cybersecurity": 20,
    # Standards bodies
    "csa": 15,
    "cis_controls": 18,
    "owasp_compliance": 15,
    "isaca": 15,
    # Research
    "sans_compliance": 12,
    "gartner_compliance": 10,
    "forrester_compliance": 10,
    # Tier 2 — vendor compliance
    "microsoft_compliance": 18,
    "microsoft_compliance_blog": 15,
    "microsoft_service_trust": 18,
    "aws_compliance": 18,
    "aws_compliance_blog": 15,
    "gcp_compliance": 18,
    "oracle_compliance": 15,
    "sap_trust_center": 15,
    "salesforce_compliance": 15,
    "servicenow_compliance": 12,
    # Privacy
    "ico_uk": 18,
    # AI governance
    "nist_ai_rmf": 22,
    "iso_42001": 20,
}

# source_id → source_type label used in score breakdown
COMPLIANCE_SOURCE_TYPES: dict[str, str] = {
    "nist_compliance": "Regulatory",
    "cisa_guidance": "Regulatory",
    "enisa": "Regulatory",
    "ec_digital": "Regulatory",
    "uk_ncsc": "Regulatory",
    "hhs_ocr_hipaa": "Regulatory",
    "sec_cybersecurity": "Regulatory",
    "iso_compliance": "Standards Body",
    "pci_ssc": "Standards Body",
    "csa": "Standards Body",
    "cis_controls": "Standards Body",
    "owasp_compliance": "Standards Body",
    "isaca": "Standards Body",
    "iapp": "Compliance Research",
    "sans_compliance": "Compliance Research",
    "gartner_compliance": "Compliance Research",
    "forrester_compliance": "Compliance Research",
    "microsoft_compliance": "Vendor Compliance",
    "microsoft_compliance_blog": "Vendor Compliance",
    "microsoft_service_trust": "Vendor Compliance",
    "aws_compliance": "Vendor Compliance",
    "aws_compliance_blog": "Vendor Compliance",
    "gcp_compliance": "Vendor Compliance",
    "oracle_compliance": "Vendor Compliance",
    "sap_trust_center": "Vendor Compliance",
    "salesforce_compliance": "Vendor Compliance",
    "servicenow_compliance": "Vendor Compliance",
    "edpb": "Privacy Regulator",
    "ico_uk": "Privacy Regulator",
    "eu_ai_act": "AI Governance",
    "nist_ai_rmf": "AI Governance",
    "iso_42001": "AI Governance",
}

DEFAULT_SOURCE_SCORE = 10

# Bonus point values
BONUS_TWO_SOURCES = 10
BONUS_THREE_PLUS_SOURCES = 15
BONUS_FRAMEWORK_UPDATE = 10
BONUS_NEW_REQUIREMENT = 12
BONUS_EFFECTIVE_DATE = 8
BONUS_DEADLINE = 10
BONUS_CONTROLS_IMPACTED = 8
BONUS_FRAMEWORK_IDENTIFIED = 5
BONUS_VERSION_EXTRACTED = 5

RISK_LEVELS: list[tuple[int, int, str]] = [
    (0, 20, "LOW"),
    (21, 40, "MEDIUM"),
    (41, 60, "HIGH"),
    (61, 80, "VERY_HIGH"),
    (81, 100, "CRITICAL"),
]


def get_source_score(source_id: str) -> int:
    return COMPLIANCE_SOURCE_SCORES.get(source_id, DEFAULT_SOURCE_SCORE)


def get_risk_level(score: int) -> str:
    for low, high, level in RISK_LEVELS:
        if low <= score <= high:
            return level
    return "CRITICAL" if score > 100 else "LOW"
