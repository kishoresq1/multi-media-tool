"""
Person 2 marketing integration hooks for Agent 9.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from openosint.customer_intelligence.models.customer_intelligence import (
    CustomerLead,
    MarketingTriggerPayload,
)

logger = logging.getLogger(__name__)

DEFAULT_MARKETING_API_URL = "http://localhost:3002"


def build_marketing_payload(lead: CustomerLead) -> MarketingTriggerPayload:
    profile = lead.lead_profile
    company_ref = profile.company_reference
    return MarketingTriggerPayload(
        lead_id=lead.id,
        name=profile.name,
        company_id=company_ref.company_id if company_ref else "",
        company=profile.company,
        company_domain=company_ref.company_domain if company_ref else "",
        role=profile.job_title,
        role_category=profile.role_category.value,
        industry=profile.industry,
        intent_score=lead.intent_score,
        lead_category=lead.lead_category.value.replace(" Lead", "").upper(),
        engaged_categories=[topic.value for topic in lead.engagement_analysis.engaged_categories],
        engaged_category_counts=lead.engagement_analysis.engaged_category_counts,
        recommended_action=lead.recommended_action,
        ai_insights=lead.ai_insights,
    )


class MarketingIntegration:
    def __init__(self, base_url: str | None = None, timeout: float = 3.0) -> None:
        self.base_url = (base_url or os.environ.get("SQ1_MARKETING_API_URL") or DEFAULT_MARKETING_API_URL).rstrip("/")
        self.timeout = timeout

    async def trigger_hot_lead(self, lead: CustomerLead) -> list[str]:
        payload = build_marketing_payload(lead)
        lead.marketing_payload = payload
        triggered: list[str] = ["Marketing Intelligence Module"]

        requests: list[tuple[str, str, dict[str, Any]]] = [
            ("Personalized Email Campaign", "/api/campaigns/generate", payload.model_dump()),
            (
                "Executive Brief Generation",
                "/api/assets/create",
                {"type": "executive_brief", "lead": payload.model_dump()},
            ),
            ("Slack Notification", "/api/comms/alert", {"platform": "slack", "lead": payload.model_dump()}),
            ("Teams Notification", "/api/comms/alert", {"platform": "teams", "lead": payload.model_dump()}),
        ]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for name, path, body in requests:
                try:
                    response = await client.post(f"{self.base_url}{path}", json=body)
                    if response.status_code < 400:
                        triggered.append(name)
                    else:
                        logger.warning("Person 2 integration returned %s for %s", response.status_code, name)
                except Exception as exc:
                    logger.info("Person 2 integration unavailable for %s: %s", name, exc)

        logger.info("Hot lead payload prepared for %s", payload.name)

        return triggered
