# openosint/data/feeds.py
"""
Cybersecurity RSS/Atom feed registry for SQ1 OSINT.

All 19 trusted feed sources. Used by search_feeds.py and the background watcher.
"""

from __future__ import annotations

FEED_SOURCES: list[dict] = [
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "domain": "bleepingcomputer.com",
        "tier": "TRUSTED",
        "focus": ["breach", "vulnerability", "malware", "ransomware"],
    },
    {
        "name": "The Hacker News",
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "domain": "thehackernews.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "threat", "breach", "compliance"],
    },
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com/feed/",
        "domain": "krebsonsecurity.com",
        "tier": "TRUSTED",
        "focus": ["breach", "fraud", "cybercrime"],
    },
    {
        "name": "SecurityWeek",
        "url": "https://feeds.feedburner.com/securityweek",
        "domain": "securityweek.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "breach", "threat", "compliance"],
    },
    {
        "name": "The Record",
        "url": "https://therecord.media/feed/",
        "domain": "therecord.media",
        "tier": "TRUSTED",
        "focus": ["threat", "breach", "policy", "ransomware"],
    },
    {
        "name": "CyberScoop",
        "url": "https://cyberscoop.com/feed/",
        "domain": "cyberscoop.com",
        "tier": "TRUSTED",
        "focus": ["policy", "threat", "breach", "government"],
    },
    {
        "name": "Security Affairs",
        "url": "https://securityaffairs.com/feed",
        "domain": "securityaffairs.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "threat", "breach", "apt"],
    },
    {
        "name": "HackRead",
        "url": "https://www.hackread.com/feed/",
        "domain": "hackread.com",
        "tier": "TRUSTED",
        "focus": ["breach", "vulnerability", "hacking"],
    },
    {
        "name": "Cyber Security News",
        "url": "https://cybersecuritynews.com/feed/",
        "domain": "cybersecuritynews.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "threat", "breach"],
    },
    {
        "name": "Microsoft Security",
        "url": "https://www.microsoft.com/en-us/security/blog/feed/",
        "domain": "microsoft.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "threat", "compliance", "patch"],
    },
    {
        "name": "CrowdStrike",
        "url": "https://www.crowdstrike.com/blog/feed/",
        "domain": "crowdstrike.com",
        "tier": "TRUSTED",
        "focus": ["threat", "apt", "malware", "threat-intelligence"],
    },
    {
        "name": "Unit 42 (Palo Alto)",
        "url": "https://unit42.paloaltonetworks.com/feed/",
        "domain": "paloaltonetworks.com",
        "tier": "TRUSTED",
        "focus": ["threat", "apt", "vulnerability", "malware"],
    },
    {
        "name": "SentinelOne",
        "url": "https://www.sentinelone.com/feed/",
        "domain": "sentinelone.com",
        "tier": "TRUSTED",
        "focus": ["threat", "malware", "ransomware", "apt"],
    },
    {
        "name": "GBHackers",
        "url": "https://gbhackers.com/feed/",
        "domain": "gbhackers.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "hacking", "breach", "malware"],
    },
    {
        "name": "Infosecurity Magazine",
        "url": "https://www.infosecurity-magazine.com/rss/news/",
        "domain": "infosecurity-magazine.com",
        "tier": "TRUSTED",
        "focus": ["breach", "compliance", "threat", "policy"],
    },
    {
        "name": "SC Magazine",
        "url": "https://www.scmagazine.com/feed/",
        "domain": "scmagazine.com",
        "tier": "TRUSTED",
        "focus": ["breach", "compliance", "vulnerability", "policy"],
    },
    {
        "name": "Graham Cluley",
        "url": "https://grahamcluley.com/feed/",
        "domain": "grahamcluley.com",
        "tier": "TRUSTED",
        "focus": ["breach", "malware", "fraud", "privacy"],
    },
    {
        "name": "SANS ISC",
        "url": "https://isc.sans.edu/rssfeed.xml",
        "domain": "isc.sans.edu",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "threat", "incident", "malware"],
    },
    {
        "name": "Threatpost",
        "url": "https://threatpost.com/feed/",
        "domain": "threatpost.com",
        "tier": "TRUSTED",
        "focus": ["vulnerability", "breach", "malware", "threat"],
    },
]

# Fast lookup by domain
FEED_DOMAINS: frozenset[str] = frozenset(f["domain"] for f in FEED_SOURCES)
