"""
Intent scoring for Agent 9 customer intelligence.
"""

from __future__ import annotations

from openosint.customer_intelligence.models.customer_intelligence import (
    EngagementAnalysis,
    IntentScoreBreakdown,
    LeadProfile,
)


ENGAGEMENT_WEIGHTS = {
    "like": 1,
    "comment": 3,
    "share": 5,
    "repost": 5,
    "follow": 5,
}

DECISION_POWER_SCORES = {
    "ciso": 25,
    "chief information security officer": 25,
    "vp security": 25,
    "vice president security": 25,
    "security director": 20,
    "director of security": 20,
    "soc manager": 15,
    "security operations center manager": 15,
    "security architect": 15,
    "compliance manager": 15,
    "security engineer": 10,
    "security analyst": 10,
}

COMPANY_FIT_SCORES = {
    "government": 25,
    "public sector": 25,
    "banking": 20,
    "financial services": 20,
    "fintech": 20,
    "critical infrastructure": 20,
    "energy": 20,
    "utilities": 20,
    "telecommunications": 20,
    "healthcare": 15,
    "insurance": 15,
    "enterprise saas": 15,
    "saas": 15,
}


def score_engagement(analysis: EngagementAnalysis) -> int:
    return (
        analysis.total_likes * ENGAGEMENT_WEIGHTS["like"]
        + analysis.total_comments * ENGAGEMENT_WEIGHTS["comment"]
        + analysis.total_shares * ENGAGEMENT_WEIGHTS["share"]
        + analysis.total_follows * ENGAGEMENT_WEIGHTS["follow"]
    )


def score_decision_power(profile: LeadProfile) -> int:
    title = profile.job_title.lower()
    label = profile.decision_power_label.lower()
    for role, score in DECISION_POWER_SCORES.items():
        if role in title or role in label:
            return score
    return 0


def score_company_fit(profile: LeadProfile) -> int:
    company_ref = profile.company_reference
    raw_tags = company_ref.raw.get("tags", []) if company_ref and company_ref.raw else []
    search_text = " ".join(
        [
            profile.industry.lower(),
            company_ref.industry.lower() if company_ref else "",
            " ".join(str(tag).lower() for tag in raw_tags),
        ]
    )

    best_score = 0
    for industry_key, score in COMPANY_FIT_SCORES.items():
        if industry_key in search_text:
            best_score = max(best_score, score)
    return best_score


def calculate_intent_score(
    profile: LeadProfile,
    analysis: EngagementAnalysis,
) -> IntentScoreBreakdown:
    engagement_score = score_engagement(analysis)
    decision_power_score = score_decision_power(profile)
    company_fit_score = score_company_fit(profile)
    total_score = engagement_score + decision_power_score + company_fit_score

    return IntentScoreBreakdown(
        engagement_score=engagement_score,
        decision_power_score=decision_power_score,
        company_fit_score=company_fit_score,
        total_score=total_score,
    )
