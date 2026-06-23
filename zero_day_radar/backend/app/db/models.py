import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class IntelPost(Base):
    """
    Single table for social/researcher posts from X, Reddit, LinkedIn, HackerNews.
    Searched using [VENDOR] + [VULNERABILITY KEYWORD], scored, sorted by latest.
    """

    __tablename__ = "intel_posts"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_intel_content_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    platform: Mapped[str] = mapped_column(String(30), index=True)  # twitter | reddit | linkedin | hackernews
    source_id: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    collection_method: Mapped[str] = mapped_column(String(30))  # api | html_scraper

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    search_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_vendors: Mapped[str] = mapped_column(Text, default="[]")
    matched_vuln_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_threat_keywords: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")

    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    threat_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class VendorAdvisoryIntel(Base):
    """
    Vendor security advisories from official sources (MSRC, Cisco, Fortinet, etc.).
    Searched using vendor + vulnerability keywords, scored, stored separately.
    """

    __tablename__ = "vendor_advisory_intel"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_advisory_intel_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_id: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100))
    vendor: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    collection_method: Mapped[str] = mapped_column(String(30))

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    matched_vendors: Mapped[str] = mapped_column(Text, default="[]")
    matched_vuln_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_threat_keywords: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vendor_advisory: Mapped[bool] = mapped_column(Boolean, default=True)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class VulnerabilityIntel(Base):
    """
    Vulnerability database intel: CVE Program, NVD, CISA KEV, GitHub PoC,
    Exploit-DB, Metasploit. Latest 30-day records stored separately.
    """

    __tablename__ = "vulnerability_intel"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_vuln_intel_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_id: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100))
    collection_method: Mapped[str] = mapped_column(String(30))

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    cve_id: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(50), nullable=True)

    matched_vendors: Mapped[str] = mapped_column(Text, default="[]")
    matched_vuln_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_threat_keywords: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")

    in_cisa_kev: Mapped[bool] = mapped_column(Boolean, default=False)
    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    has_exploit: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ComplianceIntel(Base):
    """
    Compliance intelligence: regulatory updates, framework changes, audit guidance,
    privacy rules, and AI governance from regulators, standards bodies, and vendors.
    """

    __tablename__ = "compliance_intel"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_compliance_intel_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_id: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100))
    organization: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_tier: Mapped[int] = mapped_column(Integer, default=2, index=True)
    source_subtype: Mapped[str] = mapped_column(String(30), default="regulatory", index=True)
    collection_method: Mapped[str] = mapped_column(String(30))

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    matched_compliance_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_privacy_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_audit_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_ai_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_framework_keywords: Mapped[str] = mapped_column(Text, default="[]")

    frameworks: Mapped[str] = mapped_column(Text, default="[]")
    framework_versions: Mapped[str] = mapped_column(Text, default="[]")
    effective_dates: Mapped[str] = mapped_column(Text, default="[]")
    compliance_deadlines: Mapped[str] = mapped_column(Text, default="[]")
    impacted_controls: Mapped[str] = mapped_column(Text, default="[]")

    is_new_requirement: Mapped[bool] = mapped_column(Boolean, default=False)
    is_framework_update: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class CompanyBreachIntel(Base):
    """
    Company breach and ransomware incident news from Tier 1 outlets
    (KrebsOnSecurity, BleepingComputer, SecurityWeek, The Hacker News, Ransomware.live).
    """

    __tablename__ = "company_breach_intel"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_breach_intel_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_id: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100))
    source_tier: Mapped[int] = mapped_column(Integer, default=1, index=True)
    collection_method: Mapped[str] = mapped_column(String(30))

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    affected_company: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    breach_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    matched_breach_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_vendors: Mapped[str] = mapped_column(Text, default="[]")
    matched_vuln_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_threat_keywords: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")

    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ransomware: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class ResearchBlogIntel(Base):
    """
    High-trust researcher blog posts (Project Zero, Krebs, Unit42, etc.).
    Latest vulnerability research filtered by vendor + keyword, scored separately.
    """

    __tablename__ = "research_blog_intel"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_blog_intel_hash"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    source_id: Mapped[str] = mapped_column(String(50), index=True)
    source_name: Mapped[str] = mapped_column(String(100))
    collection_method: Mapped[str] = mapped_column(String(30))

    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    matched_vendors: Mapped[str] = mapped_column(Text, default="[]")
    matched_vuln_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_threat_keywords: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")

    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)

    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ── Legacy multi-stage tables (kept for pipeline) ─────────────────────


class HuntRun(Base):
    __tablename__ = "hunt_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    products: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    stage_stats: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    social_posts: Mapped[list["ResearcherSocialPost"]] = relationship(back_populates="hunt_run")
    blog_posts: Mapped[list["ResearcherBlogPost"]] = relationship(back_populates="hunt_run")
    advisory_posts: Mapped[list["VendorAdvisoryPost"]] = relationship(back_populates="hunt_run")
    cve_findings: Mapped[list["CVEFinding"]] = relationship(back_populates="hunt_run")
    scored_posts: Mapped[list["ScoredPost"]] = relationship(back_populates="hunt_run")


class ResearcherSocialPost(Base):
    __tablename__ = "researcher_social_posts"
    __table_args__ = (UniqueConstraint("hunt_run_id", "content_hash", name="uq_social_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hunt_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("hunt_runs.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_products: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    vendors: Mapped[str] = mapped_column(Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    hunt_run: Mapped["HuntRun"] = relationship(back_populates="social_posts")


class ResearcherBlogPost(Base):
    __tablename__ = "researcher_blog_posts"
    __table_args__ = (UniqueConstraint("hunt_run_id", "content_hash", name="uq_blog_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hunt_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("hunt_runs.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_products: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    vendors: Mapped[str] = mapped_column(Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    hunt_run: Mapped["HuntRun"] = relationship(back_populates="blog_posts")


class VendorAdvisoryPost(Base):
    __tablename__ = "vendor_advisory_posts"
    __table_args__ = (UniqueConstraint("hunt_run_id", "content_hash", name="uq_advisory_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hunt_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("hunt_runs.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_products: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    vendors: Mapped[str] = mapped_column(Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    hunt_run: Mapped["HuntRun"] = relationship(back_populates="advisory_posts")


class CVEFinding(Base):
    __tablename__ = "cve_findings"
    __table_args__ = (UniqueConstraint("hunt_run_id", "content_hash", name="uq_cve_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hunt_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("hunt_runs.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cves: Mapped[str] = mapped_column(Text, default="[]")
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    in_cisa_kev: Mapped[bool] = mapped_column(Boolean, default=False)
    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_products: Mapped[str] = mapped_column(Text, default="[]")
    vendors: Mapped[str] = mapped_column(Text, default="[]")
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    hunt_run: Mapped["HuntRun"] = relationship(back_populates="cve_findings")


class ScoredPost(Base):
    __tablename__ = "scored_posts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    hunt_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("hunt_runs.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vendors: Mapped[str] = mapped_column(Text, default="[]")
    products: Mapped[str] = mapped_column(Text, default="[]")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    vulnerability_types: Mapped[str] = mapped_column(Text, default="[]")
    threat_indicators: Mapped[str] = mapped_column(Text, default="[]")
    has_poc: Mapped[bool] = mapped_column(Boolean, default=False)
    active_exploitation: Mapped[bool] = mapped_column(Boolean, default=False)
    in_cisa_kev: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vendor_advisory: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW")
    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    recency_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    sources: Mapped[str] = mapped_column(Text, default="[]")
    source_categories: Mapped[str] = mapped_column(Text, default="[]")
    collection_methods: Mapped[str] = mapped_column(Text, default="[]")
    stage_sources: Mapped[str] = mapped_column(Text, default="[]")
    correlated_count: Mapped[int] = mapped_column(Integer, default=1)
    matched_keywords: Mapped[str] = mapped_column(Text, default="[]")
    matched_products: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    hunt_run: Mapped["HuntRun"] = relationship(back_populates="scored_posts")


class UnifiedIntel(Base):
    """
    Consolidated findings from all intel tables (threat + compliance).

    Populated by: run all collection APIs → aggregate → Ollama enrich → SAINT score.
    classification: PRODUCT_VULNERABILITY | COMPANY_BREACH | UNKNOWN (SAINT classifier).
    """

    __tablename__ = "unified_intel"
    __table_args__ = (UniqueConstraint("cluster_key", name="uq_unified_cluster_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    company_name: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(150), index=True, default="")
    product_name: Mapped[str] = mapped_column(String(150), index=True, default="")
    version_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    latest_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    cves: Mapped[str] = mapped_column(Text, default="[]")
    frameworks: Mapped[str] = mapped_column(Text, default="[]")

    threat_score: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="LOW", index=True)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    classification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    score_breakdown: Mapped[str] = mapped_column(Text, default="{}")
    score_reason: Mapped[str] = mapped_column(Text, default="")
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    source_refs: Mapped[str] = mapped_column(Text, default="[]")

    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_enriched: Mapped[bool] = mapped_column(Boolean, default=False)

    cluster_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class LinkedInOAuthToken(Base):
    """Stored LinkedIn OAuth tokens for personal profile posting (Sign In with LinkedIn OIDC)."""

    __tablename__ = "linkedin_oauth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    member_sub: Mapped[str] = mapped_column(String(100), index=True)
    member_urn: Mapped[str] = mapped_column(String(120))
    display_name: Mapped[str] = mapped_column(String(200), default="")
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
