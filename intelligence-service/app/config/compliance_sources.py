"""Compliance intelligence source registry."""

# Tier 1 — regulators and standards bodies (highest trust)
TIER_1_COMPLIANCE_SOURCE_IDS: list[str] = [
    "nist_compliance",
    "iso_compliance",
    "pci_ssc",
    "enisa",
    "edpb",
    "cisa_guidance",
    "eu_ai_act",
    "iapp",
]

# Tier 2 — vendor compliance portals
TIER_2_COMPLIANCE_SOURCE_IDS: list[str] = [
    "microsoft_compliance",
    "aws_compliance",
    "gcp_compliance",
    "oracle_compliance",
    "sap_trust_center",
    "salesforce_compliance",
]

COMPLIANCE_SOURCE_IDS: list[str] = [
    # Regulatory
    "nist_compliance",
    "cisa_guidance",
    "enisa",
    "ec_digital",
    "uk_ncsc",
    "hhs_ocr_hipaa",
    "sec_cybersecurity",
    # Standards bodies
    "iso_compliance",
    "pci_ssc",
    "csa",
    "cis_controls",
    "owasp_compliance",
    "isaca",
    # Research
    "iapp",
    "sans_compliance",
    "gartner_compliance",
    "forrester_compliance",
    # Cloud & vendor compliance
    "microsoft_compliance",
    "microsoft_compliance_blog",
    "microsoft_service_trust",
    "aws_compliance",
    "aws_compliance_blog",
    "gcp_compliance",
    "oracle_compliance",
    "sap_trust_center",
    "salesforce_compliance",
    "servicenow_compliance",
    # Privacy & data protection
    "edpb",
    "ico_uk",
    # AI governance
    "eu_ai_act",
    "nist_ai_rmf",
    "iso_42001",
]

SOURCE_TIER_MAP: dict[str, int] = {
    **{sid: 1 for sid in TIER_1_COMPLIANCE_SOURCE_IDS},
    **{sid: 2 for sid in TIER_2_COMPLIANCE_SOURCE_IDS},
}

SOURCE_ORG_MAP: dict[str, str] = {
    "nist_compliance": "NIST",
    "cisa_guidance": "CISA",
    "enisa": "ENISA",
    "ec_digital": "European Commission",
    "uk_ncsc": "UK NCSC",
    "hhs_ocr_hipaa": "HHS OCR",
    "sec_cybersecurity": "SEC",
    "iso_compliance": "ISO",
    "pci_ssc": "PCI SSC",
    "csa": "Cloud Security Alliance",
    "cis_controls": "CIS",
    "owasp_compliance": "OWASP",
    "isaca": "ISACA",
    "iapp": "IAPP",
    "sans_compliance": "SANS",
    "gartner_compliance": "Gartner",
    "forrester_compliance": "Forrester",
    "microsoft_compliance": "Microsoft",
    "microsoft_compliance_blog": "Microsoft",
    "microsoft_service_trust": "Microsoft",
    "aws_compliance": "AWS",
    "aws_compliance_blog": "AWS",
    "gcp_compliance": "Google Cloud",
    "oracle_compliance": "Oracle",
    "sap_trust_center": "SAP",
    "salesforce_compliance": "Salesforce",
    "servicenow_compliance": "ServiceNow",
    "edpb": "EDPB",
    "ico_uk": "ICO UK",
    "eu_ai_act": "EU AI Act",
    "nist_ai_rmf": "NIST",
    "iso_42001": "ISO",
}

COMPLIANCE_FEED_OVERRIDES: dict[str, str] = {
    "nist_compliance": "https://www.nist.gov/news-events/cybersecurity/rss.xml",
    "cisa_guidance": "https://www.cisa.gov/cybersecurity-advisories.xml",
    "enisa": "https://www.enisa.europa.eu/media/news-items/news-wires/RSS",
    "ec_digital": "https://digital-strategy.ec.europa.eu/en/news/rss.xml",
    "uk_ncsc": "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml",
    "hhs_ocr_hipaa": "https://www.hhs.gov/about/news/index.xml",
    "sec_cybersecurity": "https://www.sec.gov/news/pressreleases.rss",
    "pci_ssc": "https://blog.pcisecuritystandards.org/rss.xml",
    "csa": "https://cloudsecurityalliance.org/blog/feed/",
    "cis_controls": "https://www.cisecurity.org/feed",
    "owasp_compliance": "https://owasp.org/news/rss/",
    "isaca": "https://www.isaca.org/resources/news-and-trends/isaca-now-blog/rss",
    "iapp": "https://iapp.org/news/rss/",
    "sans_compliance": "https://www.sans.org/blog/feed.xml",
    "microsoft_compliance_blog": "https://www.microsoft.com/en-us/security/blog/feed/",
    "aws_compliance_blog": "https://aws.amazon.com/blogs/security/feed/",
    "edpb": "https://www.edpb.europa.eu/news/news_en/rss.xml",
    "ico_uk": "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/rss/",
    "nist_ai_rmf": "https://www.nist.gov/news-events/cybersecurity/rss.xml",
}
