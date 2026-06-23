#!/usr/bin/env python3
"""Backfill SAINT classification on existing unified_intel rows."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.database import init_db
from app.db.models import UnifiedIntel
from app.processors.threat_classification_engine import ThreatClassificationEngine
from app.worker.async_runner import with_session

_classifier = ThreatClassificationEngine()


async def main() -> None:
    await init_db()

    async def _run(session):
        rows = list((await session.execute(select(UnifiedIntel))).scalars())
        print(f"Classifying {len(rows)} unified_intel rows…")
        counts: dict[str, int] = {}

        for row in rows:
            cves = json.loads(row.cves or "[]")
            result = _classifier.classify(
                row.title,
                row.summary or "",
                vendor_hint=row.vendor_name,
                product_hint=row.product_name,
                company_hint=getattr(row, "company_name", None),
                cves=cves,
            )
            row.classification = result.incident_type
            row.classification_confidence = float(result.classification_confidence)
            row.classification_reason = result.reason

            if result.incident_type == "COMPANY_BREACH":
                row.company_name = result.company_name or row.company_name
            elif result.incident_type == "PRODUCT_VULNERABILITY":
                if result.vendor_name:
                    row.vendor_name = result.vendor_name
                if result.product_name:
                    row.product_name = result.product_name

            breakdown = json.loads(row.score_breakdown or "{}")
            breakdown["classification"] = result.to_dict()
            row.score_breakdown = json.dumps(breakdown)

            counts[result.incident_type] = counts.get(result.incident_type, 0) + 1

        await session.commit()
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")

    await with_session(_run)


if __name__ == "__main__":
    asyncio.run(main())
