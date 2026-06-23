"""
Pydantic models for Agent 9 Customer Intelligence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentCategory(str, Enum):
    THREAT_INTELLIGENCE = "Threat Intelligence Posts"
    VULNERABILITY_REPORT = "Vulnerability Reports"
    BREACH_REPORT = "Breach Reports"
    COMPLIANCE_UPDATE = "Compliance Updates"
    SECURITY_RESEARCH = "Security Research"
    MISINFORMATION_CLARIFICATION = "Misinformation Clarifications"


class IntelTopic(str, Enum):
    THREAT = "THREAT"
    VULNERABILITY = "VULNERABILITY"
    BREACH = "BREACH"
    COMPLIANCE = "COMPLIANCE"
    SECURITY_RESEARCH = "SECURITY_RESEARCH"
    MISINFORMATION = "MISINFORMATION"


class EngagementType(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    REPOST = "repost"
    FOLLOW = "follow"


class RoleCategory(str, Enum):
    DECISION_MAKER = "Decision Maker"
    INFLUENCER = "Influencer"
    PRACTITIONER = "Practitioner"
    UNKNOWN = "Unknown"


class LeadCategory(str, Enum):
    HOT = "Hot Lead"
    WARM = "Warm Lead"
    INTERESTED = "Interested"
    AWARENESS = "Awareness"


class CompanyReference(BaseModel):
    company_id: str = ""
    company_name: str = ""
    company_domain: str = ""
    company_threat_score: int | None = None
    industry: str = ""
    raw: dict[str, Any] | None = None


class LinkedInEngagement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    profile_url: str = ""
    linkedin_id: str = ""
    name: str
    company: str = ""
    company_domain: str = ""
    job_title: str = ""
    industry: str = ""
    seniority: str = ""
    engagement_type: EngagementType
    content_category: ContentCategory
    intel_topic: IntelTopic | None = None
    content_id: str = ""
    content_title: str = ""
    comment_text: str = ""
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadProfile(BaseModel):
    name: str
    company: str = ""
    company_reference: CompanyReference | None = None
    job_title: str = ""
    industry: str = ""
    seniority: str = ""
    role_category: RoleCategory = RoleCategory.UNKNOWN
    decision_power_label: str = "Unknown"
    profile_url: str = ""
    linkedin_id: str = ""


class EngagementAnalysis(BaseModel):
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_follows: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    engagement_frequency: float = 0.0
    content_categories: list[ContentCategory] = Field(default_factory=list)
    engaged_categories: list[IntelTopic] = Field(default_factory=list)
    engaged_category_counts: dict[str, int] = Field(default_factory=dict)
    repeated_engagement: bool = False
    consistent_engagement: bool = False
    long_term_engagement: bool = False
    multi_category_engagement: bool = False

    @property
    def total_engagements(self) -> int:
        return self.total_likes + self.total_comments + self.total_shares + self.total_follows


class IntentScoreBreakdown(BaseModel):
    engagement_score: int = 0
    decision_power_score: int = 0
    company_fit_score: int = 0
    total_score: int = 0


class MarketingTriggerPayload(BaseModel):
    lead_id: str
    name: str
    company_id: str = ""
    company: str = ""
    company_domain: str = ""
    role: str = ""
    role_category: str = ""
    industry: str = ""
    intent_score: int
    lead_category: str
    engaged_categories: list[str] = Field(default_factory=list)
    engaged_category_counts: dict[str, int] = Field(default_factory=dict)
    recommended_action: str
    ai_insights: list[str] = Field(default_factory=list)


class CustomerLead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    lead_profile: LeadProfile
    engagement_analysis: EngagementAnalysis
    intent_score: int
    score_breakdown: IntentScoreBreakdown
    lead_category: LeadCategory
    ai_insights: list[str] = Field(default_factory=list)
    recommended_action: str
    marketing_payload: MarketingTriggerPayload | None = None
    triggered_integrations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CustomerIntelligenceRequest(BaseModel):
    engagements: list[LinkedInEngagement]
    use_company_intelligence: bool = True
    trigger_hot_lead_integrations: bool = True
    persist_leads: bool = True


class CustomerIntelligenceResponse(BaseModel):
    leads: list[CustomerLead]
    summary: dict[str, int]


class DashboardLeadSummary(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    interested: int = 0
    awareness: int = 0
    companies_identified: int
    leads: list[CustomerLead]
