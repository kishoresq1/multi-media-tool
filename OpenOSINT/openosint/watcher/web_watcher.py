# openosint/watcher/web_watcher.py
"""
Background intelligence watcher for SQ1 OSINT.

Two polling jobs run on startup via APScheduler:

  1. NVD + CISA KEV  — every 60 seconds
  2. RSS feed network (19 sources) — every 5 minutes

Both jobs store new items in TinyDB using content-addressed IDs so
re-ingestion is idempotent (no duplicates).
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_scheduler = None
_watcher_running = False

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# NVD / CISA poll
# ---------------------------------------------------------------------------


async def _poll_nvd_cisa() -> None:
    """Fetch latest NVD CVEs and CISA KEV entries and persist any new items."""
    from openosint.data.store import get_intel_latest, insert_intel, intel_exists
    from openosint.tools.search_intel import run_intel_osint

    logger.info("[watcher] Polling NVD + CISA...")
    try:
        raw = await run_intel_osint(query="", limit=10)
        existing_titles = {i.get("title", "") for i in get_intel_latest(limit=200)}
        new_count = 0

        for line in raw.splitlines():
            if not line.startswith("[+]"):
                continue
            content = line[4:].strip()
            if content in existing_titles:
                continue

            severity = "INFO"
            classification = "VULNERABILITY"
            cve_ids = []

            if "[CRITICAL]" in content:
                severity = "CRITICAL"
            elif "[HIGH]" in content:
                severity = "HIGH"
            elif "[MEDIUM]" in content:
                severity = "MEDIUM"
            elif "[LOW]" in content:
                severity = "LOW"

            cve_ids = _CVE_RE.findall(content)
            if "[CISA KEV]" in content:
                classification = "VULNERABILITY"
                severity = max(severity, "CRITICAL") if severity == "INFO" else severity

            item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, content[:200]))
            if intel_exists(item_id):
                continue

            item = {
                "id": item_id,
                "title": content[:120],
                "classification": classification,
                "severity": severity,
                "summary": content,
                "cveIds": cve_ids,
                "tags": ["nvd", "cisa", "auto-fetched"],
                "timestamp": _now_iso(),
                "sourceVerified": True,
                "isMisinformation": False,
                "usedInMarketing": False,
                "source": "nvd.nist.gov/cisa.gov",
                "sourceName": "NVD / CISA KEV",
                "sourceUrl": "",
                "contentHooks": {
                    "headline": content[:100],
                    "blogAngle": f"CVE Analysis: {content[:80]}",
                    "alertType": "advisory",
                },
            }
            insert_intel(item)
            existing_titles.add(content)
            new_count += 1

        logger.info("[watcher] NVD/CISA poll complete — %d new items.", new_count)
    except Exception as exc:
        logger.warning("[watcher] NVD/CISA poll failed: %s", exc)


# ---------------------------------------------------------------------------
# RSS feed poll
# ---------------------------------------------------------------------------


async def _poll_feeds() -> None:
    """Fetch articles from all 19 RSS feed sources and persist new intel items."""
    from openosint.data.store import insert_intel, intel_exists
    from openosint.tools.search_feeds import fetch_and_classify_feeds

    logger.info("[watcher] Polling RSS feeds...")
    try:
        items = await fetch_and_classify_feeds(
            sources=None,        # all 19 registered sources
            limit_per_feed=5,
            use_ai=True,
            timeout_seconds=25,
        )
        new_count = 0
        for item in items:
            if intel_exists(item["id"]):
                continue
            insert_intel(item)
            new_count += 1

        logger.info("[watcher] Feed poll complete — %d new items stored.", new_count)
    except Exception as exc:
        logger.warning("[watcher] Feed poll failed: %s", exc)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


async def start_watcher() -> None:
    """
    Start the background APScheduler watcher. Safe to call once on startup.

    Jobs:
      - NVD + CISA poll every 60 seconds
      - RSS feed poll every 5 minutes
    Both run immediately on startup.
    """
    global _scheduler, _watcher_running
    if _watcher_running:
        return

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        _scheduler = AsyncIOScheduler()
        _scheduler.add_job(_poll_nvd_cisa, "interval", seconds=60,  id="nvd_cisa_watcher")
        _scheduler.add_job(_poll_feeds,    "interval", seconds=300, id="feed_watcher")
        _scheduler.start()
        _watcher_running = True
        logger.info("[watcher] Started — NVD/CISA every 60s, RSS feeds every 5m.")

        # Run both immediately on startup
        await _poll_nvd_cisa()
        await _poll_feeds()
    except ImportError:
        logger.warning("[watcher] apscheduler not installed — background polling disabled.")
    except Exception as exc:
        logger.warning("[watcher] Could not start scheduler: %s", exc)


def stop_watcher() -> None:
    """Stop the background scheduler."""
    global _scheduler, _watcher_running
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
    _watcher_running = False
