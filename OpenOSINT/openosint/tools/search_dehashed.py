# openosint/tools/search_dehashed.py
"""
DeHashed credential search module.

Queries the DeHashed API to find exposed credentials, emails, usernames,
passwords, IP addresses, phone numbers, and more across hundreds of leaked
databases. Returns a formatted string; never raises on failure.

Requires DEHASHED_EMAIL and DEHASHED_API_KEY environment variables.
"""

from __future__ import annotations

import asyncio
import logging
import os

import requests

from openosint.tools.exceptions import OSINTError, ToolExecutionError

logger = logging.getLogger(__name__)

_DEHASHED_API_URL = "https://api.dehashed.com/v2/search"
_DEFAULT_TIMEOUT = 15
_DEFAULT_SIZE = 10
_USER_AGENT = "SQ1-OSINT/1.0 (security research)"

# Field prefixes supported by DeHashed query syntax
_VALID_FIELDS = frozenset({
    "email", "username", "ip_address", "name",
    "address", "phone", "password", "hashed_password", "vin",
})


def _fetch_dehashed(query: str, size: int, timeout_seconds: int) -> dict:
    """
    Query the DeHashed API.

    Parameters
    ----------
    query:
        DeHashed search query. Supports plain values (searched across all fields)
        or field-scoped syntax: ``example.com``, ``email:victim@example.com``, ``username:johndoe``,
        ``ip_address:1.2.3.4``, ``name:"John Doe"``, ``phone:+15551234567``, etc.
    size:
        Max number of results to return (1–10000; free tier capped at 10).
    timeout_seconds:
        HTTP request timeout.

    Returns
    -------
    dict
        Parsed JSON response from DeHashed.

    Raises
    ------
    OSINTError
        On missing credentials, auth failure, rate limiting, or network errors.
    """
    email = os.environ.get("DEHASHED_EMAIL", "").strip()
    api_key = os.environ.get("DEHASHED_API_KEY", "").strip()

    if not email or not api_key:
        raise OSINTError(
            "DEHASHED_EMAIL and DEHASHED_API_KEY environment variables must both be set. "
            "Sign up at https://dehashed.com to get your credentials."
        )

    try:
        response = requests.post(
            _DEHASHED_API_URL,
            json={"query": query, "size": size},
            headers={
                "Accept": "application/json",
                "Dehashed-Email": email,
                "Dehashed-Api-Key": api_key,
                "User-Agent": _USER_AGENT,
            },
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise OSINTError(f"Network error querying DeHashed: {exc}") from exc

    if response.status_code == 401:
        try:
            payload = response.json()
            detail = payload.get("error") or payload.get("message")
        except ValueError:
            detail = response.text.strip()
        if detail:
            raise OSINTError(f"DeHashed authentication/subscription error: {detail}")
        raise OSINTError("Invalid DeHashed credentials. Check DEHASHED_EMAIL and DEHASHED_API_KEY.")
    if response.status_code == 302:
        raise OSINTError(
            "DeHashed authentication failed (redirected). Verify your credentials."
        )
    if response.status_code == 429:
        raise OSINTError("DeHashed rate limit exceeded. Wait and retry.")
    if response.status_code == 400:
        raise OSINTError(f"DeHashed rejected the query '{query}'. Check your query syntax.")
    if response.status_code != 200:
        raise ToolExecutionError(f"DeHashed returned HTTP {response.status_code}.")

    return response.json()


def _format_dehashed_results(data: dict, query: str) -> str:
    """Return a structured string of DeHashed findings."""
    total = data.get("total", 0)
    entries = data.get("entries") or []

    if not entries and total == 0:
        return f"No results found in DeHashed for query: '{query}'"

    lines = [
        f"DeHashed — {total:,} total record(s) found for query: '{query}'",
        f"Showing {len(entries)} result(s):\n",
    ]

    for i, entry in enumerate(entries, 1):
        db = entry.get("database_name") or "unknown database"
        parts = [f"[{i}] Source: {db}"]

        for field in ("email", "username", "name", "phone", "address"):
            val = entry.get(field)
            if val:
                parts.append(f"    {field.capitalize()}: {val}")

        ip = entry.get("ip_address")
        if ip:
            parts.append(f"    IP: {ip}")

        pwd = entry.get("password")
        if pwd:
            parts.append(f"    Password (plaintext): {pwd}")

        hashed = entry.get("hashed_password")
        if hashed:
            short = hashed[:64] + ("..." if len(hashed) > 64 else "")
            parts.append(f"    Hashed password: {short}")

        lines.append("\n".join(parts))

    if total > len(entries):
        lines.append(f"\n... and {total - len(entries):,} more record(s) not shown.")

    return "\n".join(lines)


async def run_dehashed_osint(
    query: str,
    size: int = _DEFAULT_SIZE,
    timeout_seconds: int = _DEFAULT_TIMEOUT,
) -> str:
    """
    Search DeHashed for exposed credentials matching the query.

    Supports plain values or field-scoped DeHashed query syntax:
      - ``victim@example.com`` — search across all fields
      - ``example.com`` — domain-wide search across all fields
      - ``email:victim@example.com`` — email-specific search
      - ``username:johndoe`` — username search
      - ``ip_address:1.2.3.4`` — IP address search
      - ``name:"John Doe"`` — name search
      - ``phone:+15551234567`` — phone number search
      - ``password:hunter2`` — exposed password search

    Requires DEHASHED_EMAIL and DEHASHED_API_KEY environment variables.
    Returns a descriptive error string on failure rather than raising.

    Parameters
    ----------
    query:
        DeHashed search query (plain value or field:value syntax).
    size:
        Number of results to fetch (default 10; free tier limited).
    timeout_seconds:
        HTTP request timeout in seconds.

    Returns
    -------
    str
        Formatted result string or a descriptive error message.
    """
    logger.info("Starting DeHashed search for: %s", query)
    try:
        data = await asyncio.to_thread(_fetch_dehashed, query, size, timeout_seconds)
        result = _format_dehashed_results(data, query)
        logger.info("DeHashed search complete for: %s", query)
        return result
    except OSINTError as exc:
        logger.warning("DeHashed search failed: %s", exc)
        return f"Scan error: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error during DeHashed search.")
        return f"Internal error: {exc}"
