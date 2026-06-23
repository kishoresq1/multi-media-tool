"""
Customer Intelligence API routes for Agent 9.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from openosint.customer_intelligence.agent import CustomerIntelligenceAgent
from openosint.customer_intelligence.models.customer_intelligence import (
    CustomerIntelligenceRequest,
    CustomerIntelligenceResponse,
    DashboardLeadSummary,
    LinkedInEngagement,
)
from openosint.data import customer_leads

router = APIRouter()
agent = CustomerIntelligenceAgent()


@router.post("/analyze", response_model=CustomerIntelligenceResponse)
async def analyze_customer_intelligence(
    request: CustomerIntelligenceRequest,
) -> CustomerIntelligenceResponse:
    if not request.engagements:
        raise HTTPException(status_code=400, detail="At least one LinkedIn engagement is required.")
    return await agent.analyze(request)


@router.post("/ingest", response_model=CustomerIntelligenceResponse)
async def ingest_linkedin_engagements(
    engagements: list[LinkedInEngagement],
    trigger_hot_leads: bool = Query(default=True),
    persist_leads: bool = Query(default=True),
) -> CustomerIntelligenceResponse:
    if not engagements:
        raise HTTPException(status_code=400, detail="At least one LinkedIn engagement is required.")

    return await agent.analyze_engagements(
        engagements,
        use_company_intelligence=True,
        trigger_hot_lead_integrations=trigger_hot_leads,
        persist_leads=persist_leads,
    )


@router.get("/leads", response_model=DashboardLeadSummary)
async def get_customer_leads(limit: int = Query(default=25, ge=1, le=100)) -> DashboardLeadSummary:
    leads = customer_leads.get_all_leads(limit=limit)
    summary = customer_leads.get_summary(limit=500)
    return DashboardLeadSummary(
        total_leads=summary["total_leads"],
        hot_leads=summary["hot_leads"],
        warm_leads=summary["warm_leads"],
        interested=summary["interested"],
        awareness=summary["awareness"],
        companies_identified=summary["companies_identified"],
        leads=leads,
    )


@router.get("/summary")
async def get_customer_intelligence_summary() -> dict[str, int]:
    return customer_leads.get_summary(limit=500)
