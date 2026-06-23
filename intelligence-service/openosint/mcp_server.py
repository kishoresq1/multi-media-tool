# openosint/mcp_server.py
"""
OpenOSINT MCP Server — v2.20.0

Exposes all 18 OSINT tool capabilities plus multi-target investigation
to MCP-compliant AI clients over standard I/O. Tools include:
search_email, search_username, search_breach, search_whois, search_ip,
search_domain, generate_dorks, search_paste, search_phone, search_shodan,
search_virustotal, search_censys, search_ip2location, search_abuseipdb,
search_github, search_dns, search_dorks_live, scrape_url.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

from openosint.json_output import to_json
from openosint.tools.detect_misinfo import run_detect_misinfo_osint
from openosint.tools.generate_dorks import run_dork_osint
from openosint.tools.scan_company import run_scan_company_osint
from openosint.tools.scrape_url import run_scrape_url_osint
from openosint.tools.search_abuseipdb import run_abuseipdb_osint
from openosint.tools.search_breach import run_breach_osint
from openosint.tools.search_dehashed import run_dehashed_osint
from openosint.tools.search_feeds import run_feeds_osint
from openosint.tools.search_censys import run_censys_osint
from openosint.tools.search_dns import run_dns_osint
from openosint.tools.search_domain import run_domain_osint
from openosint.tools.search_dorks_live import run_dorks_live_osint
from openosint.tools.search_email import run_email_osint
from openosint.tools.search_github import run_github_osint
from openosint.tools.search_intel import run_intel_osint
from openosint.tools.search_ip import run_ip_osint
from openosint.tools.search_ip2location import run_ip2location_osint
from openosint.tools.search_paste import run_paste_osint
from openosint.tools.search_phone import run_phone_osint
from openosint.tools.search_shodan import run_shodan_osint
from openosint.tools.search_username import run_username_osint
from openosint.tools.search_virustotal import run_virustotal_osint
from openosint.tools.search_whois import run_whois_osint
from openosint.tools.track_post import run_track_post_osint
from openosint.tools.validate_source import run_validate_source_osint

logging.basicConfig(level=logging.INFO, format="[MCP] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
app = Server("openosint")

_JSON_PROP = {
    "json_output": {"type": "boolean", "description": "Return result as structured JSON."}
}


def _with_json(schema: dict) -> dict:
    """Return a copy of *schema* with the optional json_output property added."""
    props = dict(schema.get("properties", {}))
    props.update(_JSON_PROP)
    return {**schema, "properties": props}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_email",
            description="Enumerate accounts linked to an email using holehe.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"email": {"type": "string"}},
                    "required": ["email"],
                }
            ),
        ),
        Tool(
            name="search_username",
            description="Enumerate platforms where a username is registered using sherlock.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"username": {"type": "string"}},
                    "required": ["username"],
                }
            ),
        ),
        Tool(
            name="search_breach",
            description="Check if an email appears in data breaches via HaveIBeenPwned. Requires HIBP_API_KEY env var.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"email": {"type": "string"}},
                    "required": ["email"],
                }
            ),
        ),
        Tool(
            name="search_dehashed",
            description=(
                "Search DeHashed for exposed credentials across hundreds of leaked databases. "
                "Supports field-scoped queries: email:value, username:value, ip_address:value, "
                "name:value, phone:value, password:value, or a plain value to search all fields. "
                "Requires DEHASHED_EMAIL and DEHASHED_API_KEY env vars."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "DeHashed search query (plain or field:value syntax).",
                        },
                        "size": {
                            "type": "integer",
                            "description": "Max results to return (default 10).",
                        },
                    },
                    "required": ["query"],
                }
            ),
        ),
        Tool(
            name="search_whois",
            description="Retrieve WHOIS registration data for a domain.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"domain": {"type": "string"}},
                    "required": ["domain"],
                }
            ),
        ),
        Tool(
            name="search_ip",
            description="Retrieve geolocation and ASN data for an IP address via ipinfo.io.",
            inputSchema=_with_json(
                {"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
            ),
        ),
        Tool(
            name="search_domain",
            description="Enumerate subdomains of a target domain using sublist3r.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"domain": {"type": "string"}},
                    "required": ["domain"],
                }
            ),
        ),
        Tool(
            name="generate_dorks",
            description="Generate targeted Google dork URLs for any target (name, email, username, domain).",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"target": {"type": "string"}},
                    "required": ["target"],
                }
            ),
        ),
        Tool(
            name="search_paste",
            description="Search Pastebin dumps for an email or username via psbdmp.ws.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                }
            ),
        ),
        Tool(
            name="search_phone",
            description="Gather carrier and geolocation data for a phone number using phoneinfoga. Use E.164 format.",
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"phone": {"type": "string"}},
                    "required": ["phone"],
                }
            ),
        ),
        Tool(
            name="search_shodan",
            description=(
                "Query Shodan for host intelligence or banner search. "
                "IP address → host lookup (open ports, org, CVEs). "
                "Any other string → keyword/service search. "
                "Requires SHODAN_API_KEY env var."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                }
            ),
        ),
        Tool(
            name="search_virustotal",
            description=(
                "Check IP, domain, URL, or file hash against VirusTotal's 70+ antivirus "
                "engines and threat intelligence. Auto-detects input type. "
                "Requires VIRUSTOTAL_API_KEY env var."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"target": {"type": "string"}},
                    "required": ["target"],
                }
            ),
        ),
        Tool(
            name="search_censys",
            description=(
                "Search Censys for internet-facing infrastructure data. "
                "IP address → open ports, services, ASN, country. "
                "Domain → certificate history, SANs, issuer, first/last seen. "
                "Requires CENSYS_API_ID and CENSYS_SECRET env vars."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"target": {"type": "string"}},
                    "required": ["target"],
                }
            ),
        ),
        Tool(
            name="search_ip2location",
            description=(
                "Enhanced IP intelligence using IP2Location Security Plan. "
                "Returns geolocation, ISP, ASN, and detects VPN, proxy, Tor exit nodes, "
                "and datacenter hosting. Sponsored integration. "
                "Requires IP2LOCATION_API_KEY env var."
            ),
            inputSchema=_with_json(
                {"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
            ),
        ),
        Tool(
            name="search_abuseipdb",
            description=(
                "Check an IP address against the AbuseIPDB v2 API for abuse reputation. "
                "Returns abuse confidence score (0–100%), total reports, country, ISP, domain, "
                "and last reported timestamp. Shows a warning when score exceeds 50%. "
                "Requires ABUSEIPDB_API_KEY env var."
            ),
            inputSchema=_with_json(
                {"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
            ),
        ),
        Tool(
            name="search_github",
            description=(
                "Search GitHub for a username, email, or keyword. "
                "For exact username matches: returns full profile, recent repos, and emails "
                "discovered from commit history. For other queries: top 5 matching accounts. "
                "Optional GITHUB_TOKEN env var raises rate limit from 60 to 5000 req/h."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                }
            ),
        ),
        Tool(
            name="search_dns",
            description=(
                "Comprehensive DNS record enumeration (A, AAAA, MX, NS, TXT, CNAME, SOA). "
                "Highlights email security misconfigurations: missing SPF, weak SPF policy, "
                "missing or unenforced DMARC, and absent DKIM across common selectors. "
                "No external API or credentials required."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"domain": {"type": "string"}},
                    "required": ["domain"],
                }
            ),
        ),
        Tool(
            name="search_dorks_live",
            description=(
                "Execute Google dork queries for a target via the Bright Data SERP API, "
                "returning live structured results (title, URL, snippet). "
                "Runs up to 5 dorks by default — each is a billable API call. "
                "Requires BRIGHTDATA_API_KEY and BRIGHTDATA_SERP_ZONE env vars."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"target": {"type": "string"}},
                    "required": ["target"],
                }
            ),
        ),
        Tool(
            name="scrape_url",
            description=(
                "Fetch any public URL through the Bright Data Web Unlocker API, bypassing "
                "Cloudflare, CAPTCHA, and bot-protection. Returns the page as clean Markdown. "
                "Requires BRIGHTDATA_API_KEY and BRIGHTDATA_UNLOCKER_ZONE env vars."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"url": {"type": "string"}},
                    "required": ["url"],
                }
            ),
        ),
        Tool(
            name="investigate_multi",
            description=(
                "Investigate multiple targets in parallel using the full OSINT tool chain. "
                "Each target gets its own report file. A summary report is also generated. "
                "Maximum 10 targets. Requires ANTHROPIC_API_KEY env var."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of OSINT targets (emails, usernames, domains, IPs). Max 10.",
                    }
                },
                "required": ["targets"],
            },
        ),
        # ── SQ1 OSINT: new tools ────────────────────────────────────────────
        Tool(
            name="search_intel",
            description=(
                "Fetch cybersecurity threat intelligence from NVD and the CISA Known Exploited "
                "Vulnerabilities feed. Optional keyword filter and classification (ALL, "
                "VULNERABILITY, THREAT, COMPLIANCE, BREACH)."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keyword to filter CVEs (e.g. 'ransomware', 'apache').",
                        },
                        "classification": {
                            "type": "string",
                            "description": "Filter: ALL | VULNERABILITY | THREAT | COMPLIANCE | BREACH",
                            "default": "ALL",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max items to return (default 10).",
                            "default": 10,
                        },
                    },
                    "required": [],
                }
            ),
        ),
        Tool(
            name="validate_source",
            description=(
                "Check whether a URL or domain is a trusted cybersecurity intelligence source. "
                "Returns TRUSTED, LIKELY_TRUSTED, UNKNOWN, SUSPICIOUS, or INVALID."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {"url": {"type": "string", "description": "URL or domain to validate."}},
                    "required": ["url"],
                }
            ),
        ),
        Tool(
            name="detect_misinfo",
            description=(
                "Use Claude to analyse a cybersecurity claim or article for misinformation. "
                "Returns a JSON verdict: LEGITIMATE | MISINFORMATION | UNVERIFIED, confidence "
                "score, reasoning, and recommended action. Requires ANTHROPIC_API_KEY."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Article text or claim to analyse.",
                        },
                        "source_url": {
                            "type": "string",
                            "description": "Optional URL where the content was found.",
                        },
                    },
                    "required": ["content"],
                }
            ),
        ),
        Tool(
            name="scan_company",
            description=(
                "Run a full company OSINT scan: WHOIS, subdomain enumeration, Google dork "
                "generation, and optional breach check. Orchestrates multiple existing tools."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "company_name": {"type": "string", "description": "Human-readable company name."},
                        "domain": {"type": "string", "description": "Target domain (e.g. example.com)."},
                        "contact_email": {
                            "type": "string",
                            "description": "Optional admin/contact email for breach check.",
                        },
                    },
                    "required": ["company_name", "domain"],
                }
            ),
        ),
        Tool(
            name="track_post",
            description=(
                "Search Reddit for the same cybersecurity story to identify competitors "
                "and measure engagement. Provide a story title or CVE ID."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "story_title": {
                            "type": "string",
                            "description": "Story headline or description.",
                        },
                        "cve_id": {
                            "type": "string",
                            "description": "Optional CVE ID — used as search query when provided.",
                        },
                    },
                    "required": ["story_title"],
                }
            ),
        ),
        Tool(
            name="search_feeds",
            description=(
                "Fetch and AI-classify the latest cybersecurity news from 19 trusted RSS sources: "
                "BleepingComputer, The Hacker News, Krebs on Security, SecurityWeek, The Record, "
                "CyberScoop, Security Affairs, HackRead, Cyber Security News, Microsoft Security, "
                "CrowdStrike, Unit 42, SentinelOne, GBHackers, Infosecurity Magazine, SC Magazine, "
                "Graham Cluley, SANS ISC, and Threatpost. "
                "Returns articles classified as VULNERABILITY / THREAT / BREACH / COMPLIANCE / MISINFORMATION "
                "with CVE IDs, severity, tags, and content hooks for marketing generation."
            ),
            inputSchema=_with_json(
                {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Optional keyword filter (e.g. 'ransomware', 'Microsoft').",
                        },
                        "source_filter": {
                            "type": "string",
                            "description": "Optional source name to restrict (e.g. 'BleepingComputer').",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max articles to return across all sources (default 20).",
                        },
                    },
                    "required": [],
                }
            ),
        ),
    ]


# Map tool name → (coroutine factory, target key for JSON export)
_HANDLERS: dict[str, tuple] = {
    "search_email": (
        lambda a: run_email_osint(a["email"], timeout_seconds=120),
        lambda a: a["email"],
    ),
    "search_username": (
        lambda a: run_username_osint(a["username"], timeout_seconds=180),
        lambda a: a["username"],
    ),
    "search_breach": (
        lambda a: run_breach_osint(a["email"], timeout_seconds=15),
        lambda a: a["email"],
    ),
    "search_dehashed": (
        lambda a: run_dehashed_osint(a["query"], size=int(a.get("size", 10)), timeout_seconds=15),
        lambda a: a["query"],
    ),
    "search_whois": (
        lambda a: run_whois_osint(a["domain"], timeout_seconds=15),
        lambda a: a["domain"],
    ),
    "search_ip": (lambda a: run_ip_osint(a["ip"], timeout_seconds=10), lambda a: a["ip"]),
    "search_domain": (
        lambda a: run_domain_osint(a["domain"], timeout_seconds=120),
        lambda a: a["domain"],
    ),
    "generate_dorks": (lambda a: run_dork_osint(a["target"]), lambda a: a["target"]),
    "search_paste": (
        lambda a: run_paste_osint(a["query"], timeout_seconds=15),
        lambda a: a["query"],
    ),
    "search_phone": (
        lambda a: run_phone_osint(a["phone"], timeout_seconds=60),
        lambda a: a["phone"],
    ),
    "search_shodan": (
        lambda a: run_shodan_osint(a["query"], timeout_seconds=30),
        lambda a: a["query"],
    ),
    "search_virustotal": (
        lambda a: run_virustotal_osint(a["target"], timeout_seconds=30),
        lambda a: a["target"],
    ),
    "search_censys": (
        lambda a: run_censys_osint(a["target"], timeout_seconds=30),
        lambda a: a["target"],
    ),
    "search_ip2location": (
        lambda a: run_ip2location_osint(a["ip"], timeout_seconds=30),
        lambda a: a["ip"],
    ),
    "search_abuseipdb": (
        lambda a: run_abuseipdb_osint(a["ip"], timeout_seconds=30),
        lambda a: a["ip"],
    ),
    "search_github": (
        lambda a: run_github_osint(a["query"], timeout_seconds=30),
        lambda a: a["query"],
    ),
    "search_dns": (
        lambda a: run_dns_osint(a["domain"], timeout_seconds=10),
        lambda a: a["domain"],
    ),
    "search_dorks_live": (
        lambda a: run_dorks_live_osint(a["target"], timeout_seconds=30),
        lambda a: a["target"],
    ),
    "scrape_url": (
        lambda a: run_scrape_url_osint(a["url"], timeout_seconds=60),
        lambda a: a["url"],
    ),
    # ── SQ1 OSINT: new tool handlers ───────────────────────────────────────
    "search_intel": (
        lambda a: run_intel_osint(
            query=a.get("query", ""),
            classification=a.get("classification", "ALL"),
            limit=int(a.get("limit", 10)),
        ),
        lambda a: a.get("query", "intel"),
    ),
    "validate_source": (
        lambda a: run_validate_source_osint(a["url"]),
        lambda a: a["url"],
    ),
    "detect_misinfo": (
        lambda a: run_detect_misinfo_osint(a["content"], source_url=a.get("source_url", "")),
        lambda a: a.get("source_url", "content"),
    ),
    "scan_company": (
        lambda a: run_scan_company_osint(
            company_name=a["company_name"],
            domain=a["domain"],
            contact_email=a.get("contact_email", ""),
        ),
        lambda a: a["domain"],
    ),
    "search_feeds": (
        lambda a: run_feeds_osint(
            query=a.get("query", ""),
            source_filter=a.get("source_filter", ""),
            limit=int(a.get("limit", 20)),
        ),
        lambda a: a.get("query") or a.get("source_filter") or "all-feeds",
    ),
    "track_post": (
        lambda a: run_track_post_osint(
            story_title=a["story_title"],
            cve_id=a.get("cve_id", ""),
        ),
        lambda a: a.get("cve_id") or a["story_title"],
    ),
}


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    logger.info("Tool: %s | args: %s", name, arguments)
    should_use_json = bool(arguments.get("json_output", False))

    # Special handler for multi-target investigation
    if name == "investigate_multi":
        return await _call_investigate_multi(arguments)

    try:
        if name not in _HANDLERS:
            raise ValueError(f"Unknown tool: '{name}'")
        handler, target_fn = _HANDLERS[name]
        result = await handler(arguments)
        if should_use_json:
            target = target_fn(arguments)
            text = to_json(name, target, result)
        else:
            text = result
        return CallToolResult(content=[TextContent(type="text", text=text)], isError=False)
    except (KeyError, ValueError) as exc:
        logger.error("Validation error: %s", exc)
        return CallToolResult(content=[TextContent(type="text", text=str(exc))], isError=True)
    except Exception as exc:
        logger.exception("Unhandled error in tool '%s'.", name)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Internal error: {exc}")],
            isError=True,
        )


async def _call_investigate_multi(arguments: dict[str, Any]) -> CallToolResult:
    from openosint.multi_target import MAX_TARGETS, run_multi_target

    targets = arguments.get("targets", [])
    if not isinstance(targets, list) or not targets:
        return CallToolResult(
            content=[TextContent(type="text", text="'targets' must be a non-empty list.")],
            isError=True,
        )
    if len(targets) > MAX_TARGETS:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Too many targets ({len(targets)}). Maximum is {MAX_TARGETS}.",
                )
            ],
            isError=True,
        )
    try:
        summary = await run_multi_target(targets, is_pdf_disabled=True)
        return CallToolResult(content=[TextContent(type="text", text=summary)], isError=False)
    except Exception as exc:
        logger.exception("Error in investigate_multi.")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Internal error: {exc}")],
            isError=True,
        )


async def _serve() -> None:
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


def main() -> None:
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
