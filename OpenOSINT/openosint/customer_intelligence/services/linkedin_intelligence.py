"""
LinkedIn engagement normalization and analysis for Agent 9.

The module processes LinkedIn engagement data supplied to SQ1. It does not
scrape LinkedIn or perform external discovery.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from typing import Iterable

from openosint.customer_intelligence.models.customer_intelligence import (
    CompanyReference,
    ContentCategory,
    EngagementAnalysis,
    EngagementType,
    IntelTopic,
    LeadProfile,
    LinkedInEngagement,
    RoleCategory,
)


DECISION_MAKER_TITLES = (
    "ciso",
    "chief information security officer",
    "vp security",
    "vice president security",
    "security director",
    "director of security",
)
INFLUENCER_TITLES = ("security architect", "soc manager", "compliance manager")
PRACTITIONER_TITLES = ("security engineer", "security analyst")

TOPIC_BY_CATEGORY = {
    ContentCategory.THREAT_INTELLIGENCE: IntelTopic.THREAT,
    ContentCategory.VULNERABILITY_REPORT: IntelTopic.VULNERABILITY,
    ContentCategory.BREACH_REPORT: IntelTopic.BREACH,
    ContentCategory.COMPLIANCE_UPDATE: IntelTopic.COMPLIANCE,
    ContentCategory.SECURITY_RESEARCH: IntelTopic.SECURITY_RESEARCH,
    ContentCategory.MISINFORMATION_CLARIFICATION: IntelTopic.MISINFORMATION,
}


def normalize_engagement(raw: dict) -> LinkedInEngagement:
    engagement_type = str(raw.get("engagement_type") or raw.get("type") or "").lower()
    engagement_aliases = {"shares": "share", "reposts": "repost", "follows": "follow"}
    engagement_type = engagement_aliases.get(engagement_type, engagement_type)
    if engagement_type not in {item.value for item in EngagementType}:
        raise ValueError(f"Unsupported LinkedIn engagement type: {engagement_type}")

    category = raw.get("content_category") or raw.get("category")
    if category not in {item.value for item in ContentCategory}:
        raise ValueError(f"Unsupported SQ1 content category: {category}")

    topic = raw.get("intel_topic")
    if topic:
        topic = str(topic).upper()
        if topic not in {item.value for item in IntelTopic}:
            raise ValueError(f"Unsupported SQ1 intel topic: {topic}")

    occurred_at = raw.get("occurred_at") or raw.get("timestamp")
    parsed_time = occurred_at
    if isinstance(occurred_at, str):
        parsed_time = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))

    return LinkedInEngagement(
        profile_url=raw.get("profile_url", ""),
        linkedin_id=raw.get("linkedin_id", ""),
        name=raw["name"],
        company=raw.get("company", ""),
        company_domain=raw.get("company_domain", ""),
        job_title=raw.get("job_title", ""),
        industry=raw.get("industry", ""),
        seniority=raw.get("seniority", ""),
        engagement_type=EngagementType(engagement_type),
        content_category=ContentCategory(category),
        intel_topic=IntelTopic(topic) if topic else None,
        content_id=raw.get("content_id", ""),
        content_title=raw.get("content_title", ""),
        comment_text=raw.get("comment_text", ""),
        occurred_at=parsed_time or datetime.utcnow(),
        metadata=raw.get("metadata", {}),
    )


def group_engagements_by_profile(
    engagements: Iterable[LinkedInEngagement],
) -> dict[str, list[LinkedInEngagement]]:
    grouped: dict[str, list[LinkedInEngagement]] = defaultdict(list)
    for engagement in engagements:
        key = (
            engagement.linkedin_id
            or engagement.profile_url
            or f"{engagement.name}|{engagement.company}|{engagement.company_domain}"
        )
        grouped[key.lower()].append(engagement)
    return dict(grouped)


def normalize_intel_topic(engagement: LinkedInEngagement) -> IntelTopic:
    return engagement.intel_topic or TOPIC_BY_CATEGORY[engagement.content_category]


def classify_role(job_title: str) -> tuple[RoleCategory, str]:
    title = job_title.lower()
    if any(role in title for role in DECISION_MAKER_TITLES):
        return RoleCategory.DECISION_MAKER, "Decision Maker"
    if any(role in title for role in INFLUENCER_TITLES):
        return RoleCategory.INFLUENCER, "Influencer"
    if any(role in title for role in PRACTITIONER_TITLES):
        return RoleCategory.PRACTITIONER, "Practitioner"
    return RoleCategory.UNKNOWN, "Unknown"


def build_company_reference(
    engagement: LinkedInEngagement,
    company_intelligence: dict | None,
) -> CompanyReference | None:
    if not company_intelligence and not (engagement.company or engagement.company_domain):
        return None

    company_intelligence = company_intelligence or {}
    return CompanyReference(
        company_id=str(company_intelligence.get("id", "")),
        company_name=str(company_intelligence.get("name") or engagement.company),
        company_domain=str(company_intelligence.get("domain") or engagement.company_domain),
        company_threat_score=company_intelligence.get("threatScore"),
        industry=str(company_intelligence.get("industry") or engagement.industry),
        raw=company_intelligence or None,
    )


def build_lead_profile(
    engagements: list[LinkedInEngagement],
    company_intelligence: dict | None = None,
) -> LeadProfile:
    latest = max(engagements, key=lambda item: item.occurred_at)
    role_category, decision_power_label = classify_role(latest.job_title)
    company_ref = build_company_reference(latest, company_intelligence)
    industry = latest.industry or (company_ref.industry if company_ref else "")

    return LeadProfile(
        name=latest.name,
        company=(company_ref.company_name if company_ref else latest.company),
        company_reference=company_ref,
        job_title=latest.job_title,
        industry=industry,
        seniority=latest.seniority,
        role_category=role_category,
        decision_power_label=decision_power_label,
        profile_url=latest.profile_url,
        linkedin_id=latest.linkedin_id,
    )


def analyze_engagement(engagements: list[LinkedInEngagement]) -> EngagementAnalysis:
    sorted_engagements = sorted(engagements, key=lambda item: item.occurred_at)
    timestamps = [item.occurred_at for item in sorted_engagements]
    categories = sorted({item.content_category for item in sorted_engagements}, key=lambda item: item.value)
    topic_counter = Counter(normalize_intel_topic(item).value for item in sorted_engagements)
    engaged_topics = [IntelTopic(topic) for topic in sorted(topic_counter)]

    total_likes = sum(1 for item in sorted_engagements if item.engagement_type == EngagementType.LIKE)
    total_comments = sum(1 for item in sorted_engagements if item.engagement_type == EngagementType.COMMENT)
    total_shares = sum(
        1
        for item in sorted_engagements
        if item.engagement_type in {EngagementType.SHARE, EngagementType.REPOST}
    )
    total_follows = sum(1 for item in sorted_engagements if item.engagement_type == EngagementType.FOLLOW)

    first_seen = timestamps[0] if timestamps else None
    last_seen = timestamps[-1] if timestamps else None
    frequency = 0.0
    long_term = False
    consistent = False

    if first_seen and last_seen:
        days = max((last_seen - first_seen).days + 1, 1)
        frequency = round(len(sorted_engagements) / days, 2)
        long_term = days >= 30 and len(sorted_engagements) >= 3

    if len(timestamps) >= 3:
        gaps = [
            max((timestamps[index] - timestamps[index - 1]).days, 0)
            for index in range(1, len(timestamps))
        ]
        consistent = bool(gaps) and mean(gaps) <= 14

    return EngagementAnalysis(
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        total_follows=total_follows,
        first_seen=first_seen,
        last_seen=last_seen,
        engagement_frequency=frequency,
        content_categories=categories,
        engaged_categories=engaged_topics,
        engaged_category_counts=dict(topic_counter),
        repeated_engagement=len(sorted_engagements) >= 2,
        consistent_engagement=consistent,
        long_term_engagement=long_term,
        multi_category_engagement=len(engaged_topics) >= 2,
    )
