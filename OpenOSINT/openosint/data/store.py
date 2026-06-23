# openosint/data/store.py
"""
TinyDB wrapper for SQ1 OSINT persistent storage.

Tables:
  intel     — threat intelligence items
  companies — tracked companies
  employees — tracked employees
"""

from __future__ import annotations

import os
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

_DB_PATH = Path(os.environ.get("SQ1_DB_PATH", Path.home() / ".sq1-osint" / "db.json"))


def _get_db() -> TinyDB:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(_DB_PATH, storage=CachingMiddleware(JSONStorage))


# ---------------------------------------------------------------------------
# Intel helpers
# ---------------------------------------------------------------------------


def insert_intel(item: dict) -> int:
    """Insert a new intel item and return its doc_id."""
    with _get_db() as db:
        return db.table("intel").insert(item)


def get_intel_latest(limit: int = 10) -> list[dict]:
    """Return the most recent intel items."""
    with _get_db() as db:
        items = db.table("intel").all()
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:limit]


def get_intel_by_type(classification: str) -> list[dict]:
    """Return intel filtered by classification."""
    Intel = Query()
    with _get_db() as db:
        return db.table("intel").search(Intel.classification == classification.upper())


def get_intel_unmarketed() -> list[dict]:
    """Return intel items not yet used in a marketing campaign."""
    Intel = Query()
    with _get_db() as db:
        return db.table("intel").search(Intel.usedInMarketing == False)  # noqa: E712


def get_intel_marketing_queue() -> list[dict]:
    """Return intel explicitly approved for the marketing queue."""
    Intel = Query()
    with _get_db() as db:
        items = db.table("intel").search(
            (Intel.readyForMarketing == True)  # noqa: E712
            & (Intel.usedInMarketing == False)  # noqa: E712
            & (Intel.isMisinformation != True)  # noqa: E712
        )
    items.sort(key=lambda x: x.get("marketingPushedAt") or x.get("timestamp", ""), reverse=True)
    return items


def mark_intel_ready_for_marketing(item_id: str, pushed_at: str) -> bool:
    """Approve an intel item for the marketing queue. Returns True if found."""
    Intel = Query()
    with _get_db() as db:
        tbl = db.table("intel")
        result = tbl.update(
            {
                "readyForMarketing": True,
                "marketingPushedAt": pushed_at,
                "usedInMarketing": False,
            },
            Intel.id == item_id,
        )
        return bool(result)


def mark_intel_used(item_id: str) -> bool:
    """Mark an intel item as used in marketing. Returns True if found."""
    Intel = Query()
    with _get_db() as db:
        tbl = db.table("intel")
        result = tbl.update(
            {"usedInMarketing": True, "readyForMarketing": False},
            Intel.id == item_id,
        )
        return bool(result)


def search_intel(keyword: str) -> list[dict]:
    """Full-text search across title and summary fields."""
    keyword_lower = keyword.lower()
    with _get_db() as db:
        items = db.table("intel").all()
    return [
        i for i in items
        if keyword_lower in i.get("title", "").lower()
        or keyword_lower in i.get("summary", "").lower()
    ]


def get_intel_by_id(item_id: str) -> dict | None:
    """Return a single intel item by its id field."""
    Intel = Query()
    with _get_db() as db:
        results = db.table("intel").search(Intel.id == item_id)
    return results[0] if results else None


def intel_exists(item_id: str) -> bool:
    """Return True if an intel item with this id already exists (dedup check)."""
    return get_intel_by_id(item_id) is not None


def purge_seeded_intel() -> int:
    """Remove hardcoded seed/demo intel items from the DB.

    Demo items are identified by having no 'sourceName' key, which is only
    present on items written by the live watcher or feed scan.  Returns the
    number of items removed.
    """
    with _get_db() as db:
        tbl = db.table("intel")
        all_items = tbl.all()
        ids_to_remove = [
            item.doc_id
            for item in all_items
            if "sourceName" not in item
        ]
        if ids_to_remove:
            tbl.remove(doc_ids=ids_to_remove)
    return len(ids_to_remove)


def get_intel_by_source(source_domain: str, limit: int = 50) -> list[dict]:
    """Return intel items from a specific source domain."""
    Intel = Query()
    with _get_db() as db:
        items = db.table("intel").search(Intel.source == source_domain)
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items[:limit]


def get_intel_stats() -> dict:
    """Return counts by classification and severity for the dashboard."""
    with _get_db() as db:
        items = db.table("intel").all()
    stats: dict = {
        "total": len(items),
        "by_classification": {},
        "by_severity": {},
        "unmarketed": 0,
        "misinformation": 0,
    }
    for item in items:
        cls = item.get("classification", "UNKNOWN")
        sev = item.get("severity", "UNKNOWN")
        stats["by_classification"][cls] = stats["by_classification"].get(cls, 0) + 1
        stats["by_severity"][sev] = stats["by_severity"].get(sev, 0) + 1
        if not item.get("usedInMarketing"):
            stats["unmarketed"] += 1
        if item.get("isMisinformation"):
            stats["misinformation"] += 1
    return stats


# ---------------------------------------------------------------------------
# Company helpers
# ---------------------------------------------------------------------------


def insert_company(company: dict) -> int:
    with _get_db() as db:
        return db.table("companies").insert(company)


def get_all_companies() -> list[dict]:
    with _get_db() as db:
        return db.table("companies").all()


def get_company(company_id: str) -> dict | None:
    Company = Query()
    with _get_db() as db:
        results = db.table("companies").search(Company.id == company_id)
    return results[0] if results else None


def update_company(company_id: str, data: dict) -> bool:
    Company = Query()
    with _get_db() as db:
        result = db.table("companies").update(data, Company.id == company_id)
    return bool(result)


# ---------------------------------------------------------------------------
# Employee helpers
# ---------------------------------------------------------------------------


def insert_employee(employee: dict) -> int:
    with _get_db() as db:
        return db.table("employees").insert(employee)


def get_employees_by_company(company_id: str) -> list[dict]:
    Employee = Query()
    with _get_db() as db:
        return db.table("employees").search(Employee.companyId == company_id)


def get_employee_by_email(email: str) -> dict | None:
    Employee = Query()
    with _get_db() as db:
        results = db.table("employees").search(Employee.email == email)
    return results[0] if results else None


def update_employee(email: str, data: dict) -> bool:
    Employee = Query()
    with _get_db() as db:
        result = db.table("employees").update(data, Employee.email == email)
    return bool(result)
