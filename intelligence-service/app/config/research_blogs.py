"""High-trust researcher blog sources for vulnerability intelligence."""

RESEARCH_BLOG_SOURCE_IDS: list[str] = [
    "project_zero",
    "watchtowr",
    "unit42",
    "dfir_report",
    "sophos_xops",
    "orange_cyberdefense",
    "sans_isc",
    "rapid7",
    "tenable",
]

# Alternate feed URLs when primary RSS fails
BLOG_FEED_OVERRIDES: dict[str, str] = {
    "tenable": "https://www.tenable.com/blog/feed",
    "orange_cyberdefense": "https://www.orangecyberdefense.com/global/blog/rss.xml",
}

BLOG_SIGNAL_WORDS = [
    "vulnerability", "vulnerabilities", "cve-", "exploit", "zero-day", "zero day",
    "0day", "rce", "malware", "ransomware", "threat", "attack", "breach",
    "patch", "security flaw", "actively exploited", "in the wild", "poc",
    "authentication bypass", "privilege escalation",
]
