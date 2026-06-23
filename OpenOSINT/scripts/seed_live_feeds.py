"""Fetch and store live RSS feed intel into TinyDB."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from openosint.tools.search_feeds import fetch_and_classify_feeds
from openosint.data.feeds import FEED_SOURCES
from openosint.data.store import insert_intel, intel_exists, get_intel_stats


async def main():
    print(f"[feed-seed] Fetching from {len(FEED_SOURCES)} RSS sources...")
    print("[feed-seed] This may take ~30 seconds...")

    items = await fetch_and_classify_feeds(
        sources=FEED_SOURCES,
        limit_per_feed=5,
        use_ai=True,
        timeout_seconds=30,
    )

    print(f"[feed-seed] Fetched {len(items)} articles from feeds")

    inserted = 0
    skipped = 0
    for item in items:
        if intel_exists(item["id"]):
            skipped += 1
        else:
            insert_intel(item)
            inserted += 1

    print(f"[feed-seed] Inserted {inserted} new items, skipped {skipped} duplicates")

    stats = get_intel_stats()
    print(f"[feed-seed] DB now has {stats['total']} total intel items")
    print(f"  By classification: {stats['by_classification']}")
    print(f"  By severity: {stats['by_severity']}")
    print(f"  Unmarketed (ready for marketing): {stats['unmarketed']}")

    print("\nSample of latest items:")
    from openosint.data.store import get_intel_latest
    for item in get_intel_latest(limit=5):
        src = item.get("sourceName", item.get("source", "?"))
        print(f"  [{item['severity']}][{item['classification']}] {item['title'][:65]}")
        print(f"    Source: {src}")


asyncio.run(main())
