"""
SAINT Threat Scoring Engine — source point values (0-100 scale).
"""

# Researcher social
# X/Twitter, LinkedIn = 5 | Reddit, HackerNews = 3

# Trusted research + blogs (by source_id)
THREAT_SOURCE_SCORES: dict[str, int] = {
    # Social
    "twitter": 5,
    "linkedin": 5,
    "reddit": 3,
    "hackernews": 3,
    # Trusted research
    "project_zero": 20,
    "watchtowr": 20,
    "unit42": 20,
    "krebsonsecurity": 18,
    "bleepingcomputer": 18,
    "securityweek": 16,
    "the_hacker_news": 16,
    "ransomware_live": 22,
    # Research blogs
    "dfir_report": 15,
    "sophos_xops": 15,
    "rapid7": 15,
    "tenable": 15,
    "orange_cyberdefense": 15,
    "sans_isc": 10,
    # Conference
    "blackhat": 15,
    "defcon": 15,
    # Official / vulnerability
    "cve_program": 15,
    "nvd": 5,
    # Exploit sources
    "github_poc": 20,
    "exploit_db": 25,
    "metasploit": 25,
    "packetstorm": 20,
    # Active exploitation
    "cisa_kev": 40,
}

# All vendor advisory source IDs score 30 (Official — Vendor Advisory)
VENDOR_ADVISORY_SOURCE_IDS_FOR_SCORING: list[str] = [
    "msrc", "cisco_advisories", "fortinet_psirt", "palo_alto_advisories",
    "vmware_advisories", "ivanti_advisories", "citrix_bulletins",
    "juniper_advisories", "chrome_releases", "adobe_security", "apple_security",
    "oracle_security", "sap_security", "atlassian_security", "gitlab_security",
    "manageengine_security", "aws_security", "gcp_security", "docker_security",
    "hashicorp_security",
]

for _adv_id in VENDOR_ADVISORY_SOURCE_IDS_FOR_SCORING:
    THREAT_SOURCE_SCORES[_adv_id] = 30

# Display name / alias → score (lowercase keys)
THREAT_NAME_ALIASES: dict[str, int] = {
    "x/twitter": 5,
    "twitter": 5,
    "x": 5,
    "linkedin": 5,
    "reddit": 3,
    "hacker news": 3,
    "hackernews": 3,
    "google project zero": 20,
    "project zero": 20,
    "watchtowr": 20,
    "watchtowr labs": 20,
    "unit42": 20,
    "palo alto unit42": 20,
    "krebsonsecurity": 18,
    "bleepingcomputer": 18,
    "securityweek": 16,
    "the_hacker_news": 16,
    "ransomware_live": 22,
    "krebs": 15,
    "dfir report": 15,
    "sophos x-ops": 15,
    "sophos": 15,
    "rapid7": 15,
    "tenable": 15,
    "orange cyberdefense": 15,
    "sans isc": 10,
    "blackhat": 15,
    "black hat": 15,
    "defcon": 15,
    "vendor advisory": 30,
    "cve program": 15,
    "nvd": 5,
    "github poc": 20,
    "github": 20,
    "exploitdb": 25,
    "exploit-db": 25,
    "metasploit": 25,
    "packetstorm": 20,
    "cisa kev": 40,
    "kev": 40,
}

# source_type label → score when source_id/name not matched
THREAT_TYPE_SCORES: dict[str, int] = {
    "researcher social": 5,
    "researcher_social": 5,
    "researcher blog": 15,
    "researcher_blog": 15,
    "trusted research": 20,
    "conference": 15,
    "vendor advisory": 30,
    "vendor_advisory": 30,
    "official": 15,
    "vulnerability": 15,
    "exploit": 20,
    "active exploitation": 40,
}

DEFAULT_SOURCE_SCORE = 5

# Bonuses
BONUS_TWO_SOURCES = 10
BONUS_THREE_PLUS_SOURCES = 15
BONUS_POC_AVAILABLE = 15
BONUS_ACTIVE_EXPLOITATION = 20
BONUS_CVE_PRESENT = 10

# Re-use same risk bands as compliance
from app.config.compliance_scoring import get_risk_level  # noqa: E402


def get_source_score(
    source_id: str | None = None,
    source_name: str | None = None,
    source_type: str | None = None,
) -> int:
    """Resolve SAINT points for a source by id, name alias, or type."""
    if source_id:
        sid = source_id.lower().strip()
        if sid in THREAT_SOURCE_SCORES:
            return THREAT_SOURCE_SCORES[sid]

    if source_name:
        name = source_name.lower().strip()
        if name in THREAT_SOURCE_SCORES:
            return THREAT_SOURCE_SCORES[name]
        for alias, pts in sorted(THREAT_NAME_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in name or name in alias:
                return pts

    if source_type:
        st = source_type.lower().strip()
        if st in THREAT_TYPE_SCORES:
            return THREAT_TYPE_SCORES[st]
        for key, pts in THREAT_TYPE_SCORES.items():
            if key in st:
                return pts

    return DEFAULT_SOURCE_SCORE
