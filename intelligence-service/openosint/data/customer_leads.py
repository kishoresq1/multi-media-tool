"""
TinyDB persistence for Agent 9 customer leads.
"""

from __future__ import annotations

import os
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.middlewares import CachingMiddleware
from tinydb.storages import JSONStorage

from openosint.customer_intelligence.models.customer_intelligence import CustomerLead
from openosint.customer_intelligence.services.lead_classifier import summarize_leads

_DB_PATH = Path(
    os.environ.get("SQ1_LEADS_DB_PATH", Path.home() / ".sq1-osint" / "leads.json")
)


def _get_db() -> TinyDB:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(_DB_PATH, storage=CachingMiddleware(JSONStorage))


def _lead_key(lead: CustomerLead) -> str:
    profile = lead.lead_profile
    return (
        profile.linkedin_id
        or profile.profile_url
        or f"{profile.name}|{profile.company}".lower()
    )


def upsert_lead(lead: CustomerLead) -> bool:
    key = _lead_key(lead)
    data = lead.model_dump(mode="json")
    data["leadKey"] = key

    Lead = Query()
    with _get_db() as db:
        table = db.table("customer_leads")
        existing = table.search(Lead.leadKey == key)
        if existing:
            table.update(data, Lead.leadKey == key)
            return False
        table.insert(data)
        return True


def get_all_leads(limit: int = 100) -> list[CustomerLead]:
    with _get_db() as db:
        items = db.table("customer_leads").all()
    items.sort(key=lambda item: (item.get("intent_score", 0), item.get("updated_at", "")), reverse=True)
    return [CustomerLead.model_validate(item) for item in items[:limit]]


def get_lead(lead_id: str) -> CustomerLead | None:
    Lead = Query()
    with _get_db() as db:
        results = db.table("customer_leads").search(Lead.id == lead_id)
    return CustomerLead.model_validate(results[0]) if results else None


def get_summary(limit: int = 500) -> dict[str, int]:
    return summarize_leads(get_all_leads(limit=limit))

