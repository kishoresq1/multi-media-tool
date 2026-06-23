# openosint/tools/validate_source.py
"""
Source validation module.

Checks whether a URL/domain is a trusted cybersecurity intelligence source
using a curated whitelist and heuristic rules. Never raises on failure.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS: frozenset[str] = frozenset(
    {
        "nvd.nist.gov",
        "cisa.gov",
        "us-cert.gov",
        "cert.gov",
        "krebsonsecurity.com",
        "bleepingcomputer.com",
        "thehackernews.com",
        "darkreading.com",
        "threatpost.com",
        "securityweek.com",
        "haveibeenpwned.com",
        "exploit-db.com",
        "schneier.com",
        "portswigger.net",
        "sans.org",
        "mitre.org",
        "attack.mitre.org",
        "cve.mitre.org",
        "nist.gov",
        "recordedfuture.com",
        "crowdstrike.com",
        "mandiant.com",
        "microsoft.com",
        "techrepublic.com",
        "wired.com",
        "arstechnica.com",
    }
)

KNOWN_DISINFO: frozenset[str] = frozenset(
    {
        "infowars.com",
        "naturalnews.com",
        "zerohedge.com",
        "beforeitsnews.com",
        "yournewswire.com",
    }
)


def _extract_domain(url: str) -> str:
    """Extract the bare domain from a URL or raw domain string."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    return parsed.netloc.lower().lstrip("www.")


async def run_validate_source_osint(url: str) -> str:
    """
    Validate whether a source URL is trusted for cybersecurity intelligence.

    Returns a verdict string: TRUSTED | LIKELY_TRUSTED | UNKNOWN | SUSPICIOUS | INVALID.

    Parameters
    ----------
    url:
        URL or domain to validate.

    Returns
    -------
    str
        Verdict with a short explanation.
    """
    logger.info("Validating source: %s", url)
    if not url or not url.strip():
        return "INVALID — No URL provided."

    try:
        domain = _extract_domain(url.strip())
    except Exception as exc:
        logger.warning("Could not parse URL '%s': %s", url, exc)
        return f"INVALID — Could not parse URL: {url}"

    if not domain:
        return f"INVALID — Could not extract domain from: {url}"

    if domain in TRUSTED_DOMAINS:
        return f"TRUSTED — {domain} is a verified cybersecurity intelligence source."

    if domain in KNOWN_DISINFO:
        return (
            f"SUSPICIOUS — {domain} is known for misinformation. "
            "Do not surface this intel."
        )

    if domain.endswith(".gov"):
        return f"LIKELY_TRUSTED — {domain} is a government domain."
    if domain.endswith(".edu"):
        return f"LIKELY_TRUSTED — {domain} is an academic domain."
    if domain.endswith(".mil"):
        return f"LIKELY_TRUSTED — {domain} is a military domain."

    logger.info("Unknown domain: %s", domain)
    return (
        f"UNKNOWN — {domain} is not in the trusted whitelist. "
        "Verify manually before surfacing."
    )
