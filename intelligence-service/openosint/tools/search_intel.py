# openosint/tools/search_intel.py
"""
Threat intelligence module.

Fetches CVEs from the NVD API and known-exploited vulnerabilities from the
CISA KEV feed. Returns a formatted string; never raises on failure.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from openosint.tools.exceptions import OSINTError

logger = logging.getLogger(__name__)

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

TRUSTED_SOURCES = [
    "nvd.nist.gov",
    "cisa.gov",
    "krebsonsecurity.com",
    "bleepingcomputer.com",
    "thehackernews.com",
    "darkreading.com",
    "threatpost.com",
    "securityweek.com",
]

_VALID_CLASSIFICATIONS = {"ALL", "VULNERABILITY", "THREAT", "COMPLIANCE", "BREACH"}


async def _fetch_nvd(client: httpx.AsyncClient, query: str, limit: int) -> list[str]:
    """Fetch CVEs from the NVD API."""
    results: list[str] = []
    try:
        params: dict = {"resultsPerPage": min(limit, 20)}
        if query:
            params["keywordSearch"] = query
        resp = await client.get(NVD_API, params=params)
        if resp.status_code == 200:
            for vuln in resp.json().get("vulnerabilities", []):
                cve = vuln.get("cve", {})
                cve_id = cve.get("id", "Unknown")
                desc = cve.get("descriptions", [{}])[0].get("value", "No description")
                severity = "UNKNOWN"
                metrics = cve.get("metrics", {})
                if "cvssMetricV31" in metrics:
                    severity = metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
                elif "cvssMetricV2" in metrics:
                    severity = metrics["cvssMetricV2"][0]["baseSeverity"]
                results.append(f"[CVE][{severity}] {cve_id}: {desc[:200]}")
        else:
            results.append(f"[NVD] HTTP {resp.status_code}")
    except Exception as exc:
        results.append(f"[NVD ERROR] {exc}")
    return results


async def _fetch_cisa_kev(client: httpx.AsyncClient, limit: int) -> list[str]:
    """Fetch the latest entries from the CISA Known Exploited Vulnerabilities feed."""
    results: list[str] = []
    try:
        resp = await client.get(CISA_KEV)
        if resp.status_code == 200:
            vulns = resp.json().get("vulnerabilities", [])
            for v in vulns[-limit:]:
                results.append(
                    f"[CISA KEV][CRITICAL] {v.get('cveID')}: "
                    f"{v.get('vulnerabilityName')} — Due: {v.get('dueDate')}"
                )
        else:
            results.append(f"[CISA KEV] HTTP {resp.status_code}")
    except Exception as exc:
        results.append(f"[CISA ERROR] {exc}")
    return results


async def run_intel_osint(
    query: str = "",
    classification: str = "ALL",
    limit: int = 10,
    timeout_seconds: int = 25,
) -> str:
    """
    Fetch cybersecurity intelligence from NVD and CISA KEV.

    Parameters
    ----------
    query:
        Optional keyword to filter CVEs (e.g. "ransomware", "apache").
    classification:
        Filter by type: ALL | VULNERABILITY | THREAT | COMPLIANCE | BREACH.
    limit:
        Maximum number of items to return.
    timeout_seconds:
        HTTP request timeout in seconds.

    Returns
    -------
    str
        Formatted result string or a descriptive error message.
    """
    logger.info("Starting intel fetch: query=%r classification=%s", query, classification)
    cls = classification.upper()
    if cls not in _VALID_CLASSIFICATIONS:
        cls = "ALL"

    results: list[str] = []
    half = max(1, limit // 2)

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            nvd_task = _fetch_nvd(client, query, half)
            cisa_task = _fetch_cisa_kev(client, half)
            nvd_results, cisa_results = await asyncio.gather(nvd_task, cisa_task)

        results.extend(nvd_results)
        results.extend(cisa_results)
    except Exception as exc:
        logger.exception("Unexpected error during intel fetch.")
        return f"Internal error: {exc}"

    if not results:
        return "No intelligence found for the given parameters."

    header = f"Intelligence results ({len(results)} items)"
    if query:
        header += f" — query: '{query}'"
    output = header + ":\n\n"
    output += "\n".join(f"[+] {r}" for r in results)
    logger.info("Intel fetch complete: %d items", len(results))
    return output
