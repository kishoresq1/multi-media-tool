"""Tier 1 company breach / ransomware news sources."""

# KrebsOnSecurity is registered under researcher_blog id but collected here for breach intel.
TIER_1_COMPANY_BREACH_SOURCE_IDS: list[str] = [
    "krebsonsecurity",
    "bleepingcomputer",
    "securityweek",
    "the_hacker_news",
    "ransomware_live",
]

COMPANY_BREACH_SOURCE_IDS: list[str] = list(TIER_1_COMPANY_BREACH_SOURCE_IDS)

BREACH_FEED_OVERRIDES: dict[str, str] = {
    "krebsonsecurity": "https://krebsonsecurity.com/feed/",
    "bleepingcomputer": "https://www.bleepingcomputer.com/feed/",
    "securityweek": "https://feeds.feedburner.com/securityweek",
    "the_hacker_news": "https://feeds.feedburner.com/TheHackersNews",
    "ransomware_live": "https://www.ransomware.live/rss.xml",
}
