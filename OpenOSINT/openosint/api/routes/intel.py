# openosint/api/routes/intel.py
"""
Intelligence feed API routes.

GET  /api/intel/latest
GET  /api/intel/search?q=...
GET  /api/intel/by-type/{type}
GET  /api/intel/unmarketed
GET  /api/intel/marketing-queue
GET  /api/intel/stats
GET  /api/intel/by-source/{domain}
POST /api/intel/{id}/mark-used
POST /api/intel/{id}/push-to-marketing
POST /api/intel/scan
POST /api/intel/scan-feeds
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from openosint.data import store

router = APIRouter()

_VALID_TYPES = {"VULNERABILITY", "THREAT", "COMPLIANCE", "BREACH", "MISINFORMATION"}


@router.get("/latest")
async def get_latest_intel(limit: int = Query(default=10, ge=1, le=100)):
    """Return the most recent intel items."""
    return store.get_intel_latest(limit=limit)


@router.get("/search")
async def search_intel(q: str = Query(..., min_length=1)):
    """Full-text search across intel title and summary."""
    return store.search_intel(q)


@router.get("/unmarketed")
async def get_unmarketed():
    """Return intel items not yet used in any marketing campaign."""
    return store.get_intel_unmarketed()


@router.get("/marketing-queue")
async def get_marketing_queue():
    """Return intel explicitly approved from the SQ1 portal for marketing."""
    return store.get_intel_marketing_queue()


@router.get("/by-type/{classification}")
async def get_by_type(classification: str):
    """Return intel items filtered by classification."""
    cls = classification.upper()
    if cls not in _VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid classification '{classification}'. Valid: {sorted(_VALID_TYPES)}",
        )
    return store.get_intel_by_type(cls)


@router.post("/{item_id}/mark-used")
async def mark_intel_used(item_id: str):
    """Mark an intel item as used in a marketing campaign."""
    found = store.mark_intel_used(item_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Intel item '{item_id}' not found.")
    return {"success": True, "id": item_id, "usedInMarketing": True}


@router.get("/stats")
async def get_intel_stats():
    """Return counts by classification, severity, and marketing status."""
    return store.get_intel_stats()


@router.get("/by-source/{domain}")
async def get_by_source(domain: str, limit: int = Query(default=50, ge=1, le=200)):
    """Return intel items from a specific source domain (e.g. bleepingcomputer.com)."""
    return store.get_intel_by_source(domain, limit=limit)


@router.post("/scan")
async def trigger_scan(query: str = Query(default="")):
    """Trigger a fresh NVD/CISA intel scan and store results."""
    import re
    import uuid
    from datetime import datetime, timezone

    from openosint.tools.search_intel import run_intel_osint

    raw = await run_intel_osint(query=query, limit=10)
    existing_titles = {i.get("title", "") for i in store.get_intel_latest(limit=200)}

    new_items = []
    for line in raw.splitlines():
        if not line.startswith("[+]"):
            continue
        content = line[4:].strip()
        if content in existing_titles:
            continue

        severity = "INFO"
        classification = "VULNERABILITY"
        cve_ids = re.findall(r"CVE-\d{4}-\d+", content)

        if "[CRITICAL]" in content:
            severity = "CRITICAL"
        elif "[HIGH]" in content:
            severity = "HIGH"
        elif "[MEDIUM]" in content:
            severity = "MEDIUM"
        elif "[LOW]" in content:
            severity = "LOW"

        item = {
            "id": str(uuid.uuid4()),
            "title": content[:120],
            "classification": classification,
            "severity": severity,
            "summary": content,
            "cveIds": cve_ids,
            "tags": ["on-demand"],
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
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
        store.insert_intel(item)
        new_items.append(item)
        existing_titles.add(content)

    return {"inserted": len(new_items), "raw_output": raw}


@router.post("/{item_id}/push-to-marketing")
async def push_intel_to_marketing(item_id: str):
    """Approve an intel item so it appears in the marketing queue."""
    from datetime import datetime, timezone

    item = store.get_intel_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Intel item '{item_id}' not found.")
    if item.get("isMisinformation"):
        raise HTTPException(status_code=400, detail="Misinformation-risk intel cannot be marketed.")

    pushed_at = datetime.now(tz=timezone.utc).isoformat()
    store.mark_intel_ready_for_marketing(item_id, pushed_at)
    return {
        "success": True,
        "id": item_id,
        "readyForMarketing": True,
        "marketingPushedAt": pushed_at,
        "marketingFrontendUrl": "http://localhost:5174",
    }


@router.post("/scan-feeds")
async def trigger_feed_scan(
    source: str = Query(default="", description="Optional source name filter"),
    query: str = Query(default="", description="Optional keyword filter"),
):
    """
    Trigger an immediate RSS feed scan across all 19 cybersecurity news sources.
    AI-classifies each article and stores new items in the intel database.
    """
    from openosint.data.store import intel_exists
    from openosint.tools.search_feeds import fetch_and_classify_feeds
    from openosint.data.feeds import FEED_SOURCES

    sources = FEED_SOURCES
    if source:
        sf = source.lower()
        sources = [s for s in sources if sf in s["name"].lower() or sf in s["domain"].lower()]

    items = await fetch_and_classify_feeds(sources=sources, limit_per_feed=5, use_ai=True)

    if query:
        ql = query.lower()
        items = [i for i in items if ql in i["title"].lower() or ql in i["summary"].lower()]

    new_items = []
    for item in items:
        if not intel_exists(item["id"]):
            store.insert_intel(item)
            new_items.append(item)

    return {
        "inserted": len(new_items),
        "total_fetched": len(items),
        "sources_polled": len(sources),
        "items": new_items,
    }
