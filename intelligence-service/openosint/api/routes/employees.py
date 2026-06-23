# openosint/api/routes/employees.py
"""
Employee management and breach scan API routes.

GET  /api/employees/{company_id}
POST /api/employees/{company_id}/scan
POST /api/employees/scan-email
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from openosint.data import store

router = APIRouter()


class EmailScanRequest(BaseModel):
    email: str


@router.get("/{company_id}")
async def list_employees(company_id: str):
    """Return all employees for a company."""
    return store.get_employees_by_company(company_id)


@router.post("/{company_id}/scan")
async def scan_all_employees(company_id: str):
    """Run breach check (HIBP + DeHashed) on all employees of a company."""
    employees = store.get_employees_by_company(company_id)
    if not employees:
        raise HTTPException(status_code=404, detail=f"No employees found for company '{company_id}'.")

    from openosint.tools.search_breach import run_breach_osint
    from openosint.tools.search_dehashed import run_dehashed_osint

    results = []
    for emp in employees:
        email = emp.get("email", "")
        if not email:
            continue

        # Run HIBP and DeHashed concurrently
        hibp_result, dehashed_result = await asyncio.gather(
            run_breach_osint(email),
            run_dehashed_osint(f"email:{email}"),
        )

        breach_count = 0
        if "Found in" in hibp_result:
            try:
                breach_count = int(hibp_result.split("Found in ")[1].split(" ")[0])
            except (IndexError, ValueError):
                breach_count = 1

        store.update_employee(email, {
            "breachCount": breach_count,
            "lastBreachScan": hibp_result[:200],
            "lastDehashedScan": dehashed_result[:200],
        })
        results.append({
            "email": email,
            "hibpResult": hibp_result,
            "dehashedResult": dehashed_result,
            "breachCount": breach_count,
        })
        # HIBP rate limit: 1 request per 1,500ms
        await asyncio.sleep(1.6)

    return {"companyId": company_id, "scanned": len(results), "results": results}


@router.post("/scan-email")
async def scan_single_email(body: EmailScanRequest):
    """Run HIBP + DeHashed breach scan for a single employee email."""
    from openosint.tools.search_breach import run_breach_osint
    from openosint.tools.search_dehashed import run_dehashed_osint

    email = body.email.strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")

    # Run both sources concurrently
    breach_result, dehashed_result = await asyncio.gather(
        run_breach_osint(email),
        run_dehashed_osint(f"email:{email}"),
    )

    breach_count = 0
    if "Found in" in breach_result:
        try:
            breach_count = int(breach_result.split("Found in ")[1].split(" ")[0])
        except (IndexError, ValueError):
            breach_count = 1

    employee = store.get_employee_by_email(email)
    if employee:
        store.update_employee(email, {"breachCount": breach_count})

    return {
        "email": email,
        "breachResult": breach_result,
        "dehashedResult": dehashed_result,
        "breachCount": breach_count,
    }
