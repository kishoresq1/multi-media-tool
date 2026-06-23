"""
Lead classification and recommendations for Agent 9.
"""

from __future__ import annotations

from openosint.customer_intelligence.models.customer_intelligence import (
    CustomerLead,
    EngagementAnalysis,
    LeadCategory,
    LeadProfile,
    RoleCategory,
)


HIGH_VALUE_INDUSTRIES = {
    "banking",
    "government",
    "healthcare",
    "insurance",
    "enterprise saas",
    "critical infrastructure",
}


def classify_lead(intent_score: int) -> LeadCategory:
    if intent_score >= 90:
        return LeadCategory.HOT
    if intent_score >= 70:
        return LeadCategory.WARM
    if intent_score >= 50:
        return LeadCategory.INTERESTED
    return LeadCategory.AWARENESS


def recommend_action(category: LeadCategory, profile: LeadProfile) -> str:
    if category == LeadCategory.HOT:
        return "Schedule Security Intelligence Demo"
    if category == LeadCategory.WARM:
        return "Send personalized threat intelligence email and invite to briefing"
    if category == LeadCategory.INTERESTED:
        return "Enroll in targeted nurture sequence with relevant SQ1 research"
    return "Continue awareness retargeting with educational cybersecurity content"


def build_ai_insights(profile: LeadProfile, analysis: EngagementAnalysis) -> list[str]:
    insights: list[str] = []

    if analysis.multi_category_engagement:
        insights.append("Engaged with multiple SQ1 intelligence topics")
    if analysis.engaged_category_counts:
        top_topic = max(analysis.engaged_category_counts, key=analysis.engaged_category_counts.get)
        insights.append(f"Highest engagement topic is {top_topic}")
    if analysis.repeated_engagement:
        insights.append("Repeated engagement with SQ1 security intelligence content")
    if analysis.consistent_engagement:
        insights.append("Consistent engagement over time")
    if analysis.long_term_engagement:
        insights.append("Long-term engagement pattern detected")

    if profile.role_category == RoleCategory.DECISION_MAKER:
        insights.append("Security decision maker with direct buying influence")
    elif profile.role_category == RoleCategory.INFLUENCER:
        insights.append("Security influencer likely to shape vendor evaluation")
    elif profile.role_category == RoleCategory.PRACTITIONER:
        insights.append("Security practitioner showing hands-on interest")

    if profile.industry.lower() in HIGH_VALUE_INDUSTRIES:
        insights.append("High-value industry fit for SQ1 security intelligence")

    if profile.company_reference and profile.company_reference.company_id:
        insights.append("Matched to existing Person 1 company intelligence record")

    if not insights:
        insights.append("Early-stage LinkedIn engagement detected")

    return insights


def summarize_leads(leads: list[CustomerLead]) -> dict[str, int]:
    companies = {
        lead.lead_profile.company_reference.company_id
        or lead.lead_profile.company
        for lead in leads
        if lead.lead_profile.company_reference or lead.lead_profile.company
    }
    return {
        "total_leads": len(leads),
        "hot_leads": sum(1 for lead in leads if lead.lead_category == LeadCategory.HOT),
        "warm_leads": sum(1 for lead in leads if lead.lead_category == LeadCategory.WARM),
        "interested": sum(1 for lead in leads if lead.lead_category == LeadCategory.INTERESTED),
        "awareness": sum(1 for lead in leads if lead.lead_category == LeadCategory.AWARENESS),
        "companies_identified": len(companies),
    }
