# openosint/tools/scan_company.py
"""
Company OSINT orchestration module.

Runs a full company scan by concurrently invoking existing OpenOSINT tools:
WHOIS, subdomain enumeration, Google dork generation, and breach check.
Never raises on failure; errors are captured per-section.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_scan_company_osint(
    company_name: str,
    domain: str,
    contact_email: str = "",
    timeout_seconds: int = 120,
) -> str:
    """
    Run a full company OSINT scan orchestrating existing OpenOSINT tools.

    Combines: WHOIS + subdomain enumeration + Google dorks + domain-wide
    DeHashed exposure search + optional contact email breach checks.

    Parameters
    ----------
    company_name:
        Human-readable company name for the report header.
    domain:
        Target domain (e.g. "example.com").
    contact_email:
        Optional contact/admin email; if provided HIBP and DeHashed email checks are run.
    timeout_seconds:
        Global timeout applied to individual subtasks.

    Returns
    -------
    str
        Aggregated formatted report string.
    """
    from openosint.tools.generate_dorks import run_dork_osint
    from openosint.tools.search_breach import run_breach_osint
    from openosint.tools.search_dehashed import run_dehashed_osint
    from openosint.tools.search_domain import run_domain_osint
    from openosint.tools.search_whois import run_whois_osint

    logger.info("Starting company scan: %s (%s)", company_name, domain)

    sections: list[tuple[str, asyncio.Task]] = []

    async def _run(coro) -> str:
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return "Timed out."
        except Exception as exc:
            return f"Error: {exc}"

    tasks = [
        ("WHOIS", asyncio.create_task(_run(run_whois_osint(domain)))),
        ("SUBDOMAINS", asyncio.create_task(_run(run_domain_osint(domain)))),
        ("DORKS", asyncio.create_task(_run(run_dork_osint(domain)))),
        ("DEHASHED_DOMAIN", asyncio.create_task(_run(run_dehashed_osint(domain)))),
    ]
    if contact_email:
        tasks.append(
            ("BREACH_CHECK", asyncio.create_task(_run(run_breach_osint(contact_email))))
        )
        tasks.append(
            ("DEHASHED", asyncio.create_task(_run(run_dehashed_osint(f"email:{contact_email}"))))
        )

    results = []
    results.append(f"=== Company OSINT Scan: {company_name} ({domain}) ===\n")

    label_tasks = [(label, task) for label, task in tasks]
    gathered = await asyncio.gather(*[t for _, t in label_tasks], return_exceptions=True)

    for (label, _), result in zip(label_tasks, gathered):
        if isinstance(result, Exception):
            results.append(f"\n[{label}] ERROR: {result}")
        else:
            results.append(f"\n[{label}]\n{result}")

    logger.info("Company scan complete: %s", company_name)
    return "\n".join(results)
