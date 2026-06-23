from app.config.keyword_matcher import build_scraper_queries
from app.config.keywords import VENDOR_KEYWORDS

# Security-focused subreddits for Reddit [VENDOR] + [SEARCH_KEYWORD] search
REDDIT_SECURITY_SUBREDDITS: list[str] = [
    "netsec",
    "cybersecurity",
    "blueteamsec",
    "AskNetsec",
    "CVE",
]


def build_search_queries(
    vendors: list[str] | None = None,
    max_queries: int = 60,
) -> list[str]:
    """
    PRIMARY scraper queries: [VENDOR] + [SEARCH_KEYWORD] only.
    Fallback keywords are NOT used for query building.
    """
    return build_scraper_queries(vendors=vendors, max_queries=max_queries)


def build_reddit_queries(
    vendors: list[str] | None = None,
    max_queries: int = 30,
) -> list[tuple[str, str | None]]:
    """Reddit queries using PRIMARY SEARCH_KEYWORDS only."""
    base = build_scraper_queries(vendors=vendors, max_queries=max_queries)
    scoped: list[tuple[str, str | None]] = []

    for query in base:
        scoped.append((query, None))
        for sub in REDDIT_SECURITY_SUBREDDITS[:2]:
            scoped.append((query, sub))
            if len(scoped) >= max_queries:
                return scoped

    return scoped[:max_queries]


def build_linkedin_queries(
    vendors: list[str] | None = None,
    max_queries: int = 30,
) -> list[str]:
    return build_scraper_queries(vendors=vendors, max_queries=max_queries)


def build_hackernews_queries(
    vendors: list[str] | None = None,
    max_queries: int = 30,
) -> list[str]:
    return build_scraper_queries(vendors=vendors, max_queries=max_queries)


def to_pullpush_query(query: str) -> str:
    """Convert 'Fortinet RCE' → 'Fortinet AND RCE' for Reddit PullPush."""
    parts = query.split()
    if len(parts) < 2:
        return query

    vendor_words = []
    rest = []
    i = 0
    while i < len(parts):
        matched = False
        for vendor in sorted(VENDOR_KEYWORDS, key=len, reverse=True):
            vendor_parts = vendor.split()
            if i + len(vendor_parts) <= len(parts):
                candidate = " ".join(parts[i : i + len(vendor_parts)])
                if candidate.lower() == vendor.lower():
                    vendor_words.append(f'"{vendor}"' if " " in vendor else vendor)
                    i += len(vendor_parts)
                    matched = True
                    break
        if not matched:
            rest.append(parts[i])
            i += 1

    vendor_str = " ".join(vendor_words) if vendor_words else parts[0]
    if not rest:
        rest = parts[1:]
    if " " in vendor_str and not vendor_str.startswith('"'):
        vendor_str = f'"{vendor_str}"'
    return f"{vendor_str} AND {' AND '.join(rest)}" if rest else vendor_str
