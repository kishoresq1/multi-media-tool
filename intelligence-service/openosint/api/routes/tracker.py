# openosint/api/routes/tracker.py
"""
Post tracking API routes.

GET  /api/tracker/posts?story=...&cve=...
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from openosint.tools.track_post import run_track_post_osint

router = APIRouter()


@router.get("/posts")
async def track_posts(
    story: str = Query(default="", description="Story title or headline to track"),
    cve: str = Query(default="", description="CVE ID to search for"),
):
    """Search Reddit for competing posts about the same cybersecurity story."""
    if not story and not cve:
        return {"error": "Provide 'story' or 'cve' query parameter."}

    result = await run_track_post_osint(
        story_title=story or cve,
        cve_id=cve,
    )
    return {"query": cve or story, "raw": result}
