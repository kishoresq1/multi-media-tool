# openosint/api/routes/companies.py
"""
Company management API routes.

GET  /api/companies
GET  /api/companies/{id}
POST /api/companies
POST /api/companies/{id}/scan
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from openosint.data import store

router = APIRouter()


class CompanyIn(BaseModel):
    name: str
    domain: str
    contactEmail: str = ""
    tags: list[str] = []


@router.get("")
async def list_companies():
    """Return all tracked companies."""
    return store.get_all_companies()


@router.get("/{company_id}")
async def get_company(company_id: str):
    """Return a single company by ID."""
    company = store.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")
    return company


@router.post("")
async def add_company(body: CompanyIn):
    """Add a new company to track."""
    company = {
        "id": str(uuid.uuid4()),
        "name": body.name,
        "domain": body.domain,
        "contactEmail": body.contactEmail,
        "threatScore": 0,
        "lastScan": None,
        "employeeCount": 0,
        "tags": body.tags,
    }
    store.insert_company(company)
    return company


@router.post("/{company_id}/scan")
async def scan_company(company_id: str):
    """Trigger a full OSINT scan for a company."""
    company = store.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")

    from openosint.tools.scan_company import run_scan_company_osint

    result = await run_scan_company_osint(
        company_name=company["name"],
        domain=company["domain"],
        contact_email=company.get("contactEmail", ""),
    )

    last_scan = datetime.now(tz=timezone.utc).isoformat()
    store.update_company(company_id, {"lastScan": last_scan})

    return {"companyId": company_id, "lastScan": last_scan, "report": result}
