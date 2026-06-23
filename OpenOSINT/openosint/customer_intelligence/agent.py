"""
Agent 9: Customer Intelligence Agent.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from openosint.customer_intelligence.integrations.marketing import (
    MarketingIntegration,
    build_marketing_payload,
)
from openosint.customer_intelligence.models.customer_intelligence import (
    CustomerIntelligenceRequest,
    CustomerIntelligenceResponse,
    CustomerLead,
    LeadCategory,
    LinkedInEngagement,
)
from openosint.customer_intelligence.services.intent_scoring import calculate_intent_score
from openosint.customer_intelligence.services.lead_classifier import (
    build_ai_insights,
    classify_lead,
    recommend_action,
    summarize_leads,
)
from openosint.customer_intelligence.services.linkedin_intelligence import (
    analyze_engagement,
    build_lead_profile,
    group_engagements_by_profile,
)
from openosint.data import customer_leads

logger = logging.getLogger(__name__)


class CustomerIntelligenceAgent:
    agent_id = "agent-9"
    name = "Customer Intelligence Agent"
    data_source = "LinkedIn engagement"

    def __init__(
        self,
        company_lookup: Callable[[LinkedInEngagement], dict[str, Any] | None] | None = None,
        marketing_integration: MarketingIntegration | None = None,
    ) -> None:
        self.company_lookup = company_lookup or self._default_company_lookup
        self.marketing_integration = marketing_integration or MarketingIntegration()

    async def analyze(self, request: CustomerIntelligenceRequest) -> CustomerIntelligenceResponse:
        grouped = group_engagements_by_profile(request.engagements)
        leads: list[CustomerLead] = []

        for engagements in grouped.values():
            latest = max(engagements, key=lambda item: item.occurred_at)
            company_intelligence = (
                self.company_lookup(latest) if request.use_company_intelligence else None
            )
            profile = build_lead_profile(engagements, company_intelligence=company_intelligence)
            analysis = analyze_engagement(engagements)
            score_breakdown = calculate_intent_score(profile, analysis)
            category = classify_lead(score_breakdown.total_score)

            lead = CustomerLead(
                lead_profile=profile,
                engagement_analysis=analysis,
                intent_score=score_breakdown.total_score,
                score_breakdown=score_breakdown,
                lead_category=category,
                ai_insights=build_ai_insights(profile, analysis),
                recommended_action=recommend_action(category, profile),
                updated_at=datetime.now(timezone.utc),
            )
            lead.marketing_payload = build_marketing_payload(lead)

            if category == LeadCategory.HOT and request.trigger_hot_lead_integrations:
                lead.triggered_integrations = await self.marketing_integration.trigger_hot_lead(lead)

            if request.persist_leads:
                customer_leads.upsert_lead(lead)

            leads.append(lead)

        leads.sort(key=lambda item: item.intent_score, reverse=True)
        return CustomerIntelligenceResponse(leads=leads, summary=summarize_leads(leads))

    async def analyze_engagements(
        self,
        engagements: list[LinkedInEngagement],
        use_company_intelligence: bool = True,
        trigger_hot_lead_integrations: bool = True,
        persist_leads: bool = True,
    ) -> CustomerIntelligenceResponse:
        return await self.analyze(
            CustomerIntelligenceRequest(
                engagements=engagements,
                use_company_intelligence=use_company_intelligence,
                trigger_hot_lead_integrations=trigger_hot_lead_integrations,
                persist_leads=persist_leads,
            )
        )

    def _default_company_lookup(self, engagement: LinkedInEngagement) -> dict[str, Any] | None:
        try:
            from openosint.data import store

            company_name = engagement.company.lower()
            company_domain = engagement.company_domain.lower()
            for company in store.get_all_companies():
                name_matches = company_name and company.get("name", "").lower() == company_name
                domain_matches = company_domain and company.get("domain", "").lower() == company_domain
                if name_matches or domain_matches:
                    return company
        except Exception as exc:  # pragma: no cover - optional integration
            logger.debug("Company intelligence lookup unavailable: %s", exc)
        return None
