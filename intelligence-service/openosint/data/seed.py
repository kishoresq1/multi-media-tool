# openosint/data/seed.py
"""
Seed demo data for SQ1 OSINT.

Run: python -m openosint.data.seed
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from openosint.data.store import (
    get_all_companies,
    insert_company,
    insert_employee,
)


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _ts(offset_hours: int = 0) -> str:
    from datetime import timedelta
    dt = datetime.now(tz=timezone.utc) - timedelta(hours=offset_hours)
    return dt.isoformat()


DEMO_COMPANIES = [
    {
        "id": "c1",
        "name": "Acme Corp",
        "domain": "acme.com",
        "threatScore": 72,
        "lastScan": _ts(2),
        "employeeCount": 5,
        "tags": ["finance", "saas"],
    },
    {
        "id": "c2",
        "name": "TechNova Inc",
        "domain": "technova.io",
        "threatScore": 45,
        "lastScan": _ts(6),
        "employeeCount": 3,
        "tags": ["tech", "startup"],
    },
    {
        "id": "c3",
        "name": "MedSecure Health",
        "domain": "medsecure.health",
        "threatScore": 88,
        "lastScan": _ts(1),
        "employeeCount": 4,
        "tags": ["healthcare", "compliance"],
    },
    {
        "id": "c4",
        "name": "GlobalRetail Ltd",
        "domain": "globalretail.co",
        "threatScore": 31,
        "lastScan": _ts(12),
        "employeeCount": 3,
        "tags": ["retail", "e-commerce"],
    },
    {
        "id": "c5",
        "name": "CryptoVault",
        "domain": "cryptovault.finance",
        "threatScore": 94,
        "lastScan": _ts(0),
        "employeeCount": 3,
        "tags": ["crypto", "finance", "high-risk"],
    },
]

DEMO_EMPLOYEES = [
    {"id": str(uuid.uuid4()), "companyId": "c1", "name": "Alice Chen", "email": "alice@acme.com", "role": "CISO", "breachCount": 2, "pasteCount": 0, "servicesFound": ["LinkedIn", "Twitter"]},
    {"id": str(uuid.uuid4()), "companyId": "c1", "name": "Bob Martinez", "email": "bob@acme.com", "role": "DevOps", "breachCount": 0, "pasteCount": 1, "servicesFound": ["GitHub", "HackerNews"]},
    {"id": str(uuid.uuid4()), "companyId": "c1", "name": "Carol White", "email": "carol@acme.com", "role": "Engineer", "breachCount": 3, "pasteCount": 2, "servicesFound": ["LinkedIn", "Slack"]},
    {"id": str(uuid.uuid4()), "companyId": "c1", "name": "David Kim", "email": "david@acme.com", "role": "Finance", "breachCount": 1, "pasteCount": 0, "servicesFound": ["LinkedIn"]},
    {"id": str(uuid.uuid4()), "companyId": "c1", "name": "Eve Johnson", "email": "eve@acme.com", "role": "HR", "breachCount": 0, "pasteCount": 0, "servicesFound": []},
    {"id": str(uuid.uuid4()), "companyId": "c2", "name": "Frank Lee", "email": "frank@technova.io", "role": "CTO", "breachCount": 0, "pasteCount": 0, "servicesFound": ["GitHub", "Twitter"]},
    {"id": str(uuid.uuid4()), "companyId": "c2", "name": "Grace Patel", "email": "grace@technova.io", "role": "Backend", "breachCount": 1, "pasteCount": 0, "servicesFound": ["GitHub"]},
    {"id": str(uuid.uuid4()), "companyId": "c2", "name": "Henry Nguyen", "email": "henry@technova.io", "role": "Frontend", "breachCount": 0, "pasteCount": 1, "servicesFound": ["LinkedIn", "GitHub"]},
    {"id": str(uuid.uuid4()), "companyId": "c3", "name": "Iris Thompson", "email": "iris@medsecure.health", "role": "CTO", "breachCount": 4, "pasteCount": 3, "servicesFound": ["LinkedIn"]},
    {"id": str(uuid.uuid4()), "companyId": "c3", "name": "Jake Wilson", "email": "jake@medsecure.health", "role": "Compliance", "breachCount": 2, "pasteCount": 1, "servicesFound": ["LinkedIn", "Twitter"]},
    {"id": str(uuid.uuid4()), "companyId": "c3", "name": "Kate Brown", "email": "kate@medsecure.health", "role": "DevOps", "breachCount": 1, "pasteCount": 0, "servicesFound": ["GitHub"]},
    {"id": str(uuid.uuid4()), "companyId": "c3", "name": "Liam Davis", "email": "liam@medsecure.health", "role": "Security", "breachCount": 0, "pasteCount": 0, "servicesFound": ["LinkedIn"]},
    {"id": str(uuid.uuid4()), "companyId": "c4", "name": "Mia Garcia", "email": "mia@globalretail.co", "role": "IT Admin", "breachCount": 1, "pasteCount": 0, "servicesFound": ["LinkedIn"]},
    {"id": str(uuid.uuid4()), "companyId": "c4", "name": "Noah Harris", "email": "noah@globalretail.co", "role": "Engineer", "breachCount": 0, "pasteCount": 0, "servicesFound": ["GitHub"]},
    {"id": str(uuid.uuid4()), "companyId": "c5", "name": "Olivia Clark", "email": "olivia@cryptovault.finance", "role": "CEO", "breachCount": 5, "pasteCount": 4, "servicesFound": ["Twitter", "LinkedIn", "Telegram"]},
]


def seed() -> None:
    if get_all_companies():
        print("[seed] Database already seeded. Skipping.")
        return

    print("[seed] Inserting demo companies...")
    for company in DEMO_COMPANIES:
        insert_company(company)

    print("[seed] Inserting demo employees...")
    for emp in DEMO_EMPLOYEES:
        insert_employee(emp)

    print(f"[seed] Done: {len(DEMO_COMPANIES)} companies, {len(DEMO_EMPLOYEES)} employees. Intel will be populated from live feeds.")


if __name__ == "__main__":
    seed()
