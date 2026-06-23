"""Normalize rows from all intel SQLite tables into a common structure."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.db.models import (
    CompanyBreachIntel,
    ComplianceIntel,
    IntelPost,
    ResearchBlogIntel,
    VendorAdvisoryIntel,
    VulnerabilityIntel,
)

VERSION_PATTERN = re.compile(
    r"(?:version|v\.?)\s*(\d+(?:\.\d+){1,3})|(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)",
    re.I,
)


@dataclass
class NormalizedRecord:
    table: str
    record_id: str
    source_id: str
    source_name: str
    domain: str  # threat | compliance
    title: str
    content: str
    url: str | None
    published_at: datetime | None
    vendor: str | None = None
    product: str | None = None
    version: str | None = None
    cves: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    risk_level: str = "LOW"
    has_poc: bool = False
    active_exploitation: bool = False
    in_cisa_kev: bool = False
    is_framework_update: bool = False
    is_new_requirement: bool = False
    company: str | None = None
    is_ransomware: bool = False


def _loads(raw: str | None, default: Any = None) -> Any:
    if default is None:
        default = []
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _first_vendor(*lists: list[str]) -> str | None:
    for lst in lists:
        if lst:
            return lst[0]
    return None


def _extract_version(text: str, extra_versions: list[str] | None = None) -> str | None:
    if extra_versions:
        return extra_versions[0]
    for match in VERSION_PATTERN.finditer(text):
        val = match.group(1) or match.group(2)
        if val and len(val) <= 20:
            return val
    return None


def normalize_intel_post(row: IntelPost) -> NormalizedRecord:
    vendors = _loads(row.matched_vendors)
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="intel_posts",
        record_id=row.id,
        source_id=row.source_id or row.platform,
        source_name=row.source_name or row.platform,
        domain="threat",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=_first_vendor(vendors),
        product=None,
        version=_extract_version(text),
        cves=_loads(row.cves),
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
    )


def normalize_advisory(row: VendorAdvisoryIntel) -> NormalizedRecord:
    vendors = _loads(row.matched_vendors)
    vendor = row.vendor or _first_vendor(vendors)
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="vendor_advisory_intel",
        record_id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        domain="threat",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=vendor,
        product=None,
        version=_extract_version(text),
        cves=_loads(row.cves),
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
    )


def normalize_blog(row: ResearchBlogIntel) -> NormalizedRecord:
    vendors = _loads(row.matched_vendors)
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="research_blog_intel",
        record_id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        domain="threat",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=_first_vendor(vendors),
        version=_extract_version(text),
        cves=_loads(row.cves),
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
    )


def normalize_vulnerability(row: VulnerabilityIntel) -> NormalizedRecord:
    vendors = _loads(row.matched_vendors)
    cves = _loads(row.cves)
    if row.cve_id and row.cve_id not in cves:
        cves = [row.cve_id] + cves
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="vulnerability_intel",
        record_id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        domain="threat",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=_first_vendor(vendors),
        version=_extract_version(text),
        cves=cves,
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        has_poc=row.has_poc or row.has_exploit,
        active_exploitation=row.active_exploitation,
        in_cisa_kev=row.in_cisa_kev,
    )


def normalize_breach(row: CompanyBreachIntel) -> NormalizedRecord:
    vendors = _loads(row.matched_vendors)
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="company_breach_intel",
        record_id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        domain="threat",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=_first_vendor(vendors),
        company=row.affected_company,
        version=_extract_version(text),
        cves=_loads(row.cves),
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        has_poc=row.has_poc,
        active_exploitation=row.active_exploitation,
        is_ransomware=row.is_ransomware,
    )


def normalize_compliance(row: ComplianceIntel) -> NormalizedRecord:
    frameworks = _loads(row.frameworks)
    versions = _loads(row.framework_versions)
    org = row.organization or row.source_name
    text = f"{row.title} {row.content}"
    return NormalizedRecord(
        table="compliance_intel",
        record_id=row.id,
        source_id=row.source_id,
        source_name=row.source_name,
        domain="compliance",
        title=row.title,
        content=row.content,
        url=row.url,
        published_at=row.published_at,
        vendor=org,
        product=frameworks[0] if frameworks else None,
        version=_extract_version(text, versions),
        frameworks=frameworks,
        confidence_score=row.confidence_score,
        risk_level=row.risk_level or "LOW",
        is_framework_update=row.is_framework_update,
        is_new_requirement=row.is_new_requirement,
    )


def cluster_key_for(record: NormalizedRecord) -> str:
    if record.cves:
        return f"cve:{record.cves[0].upper()}"
    if record.table == "company_breach_intel" and record.company:
        return f"breach:{record.company.lower().strip()[:60]}:{record.title[:40].lower()}"
    vendor = (record.vendor or "unknown").lower().strip()[:60]
    product = (record.product or record.title[:40]).lower().strip()[:60]
    version = (record.version or "any").lower().strip()[:30]
    return f"{vendor}:{product}:{version}"
