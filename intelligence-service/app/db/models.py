"""
SQLAlchemy 2.0 ORM models for Intelligence_Service.

All tables use:
  - UUID primary keys (gen_random_uuid() server-side)
  - Mapped[type] / mapped_column() — no legacy Column()
  - JSONB for array/object columns (PostgreSQL-native)
  - timezone-aware DateTime columns
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

class User(Base):
    """Application users (security_team | marketing_team roles)."""

    __tablename__ = "users"
    __table_args__ = (
        sa.CheckConstraint("role IN ('security_team', 'marketing_team')", name="ck_users_role"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(sa.String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    role: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(sa.String(255))
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    # relationships
    osint_scans: Mapped[list["OsintScanResult"]] = relationship(back_populates="initiator")


# ---------------------------------------------------------------------------
# unified_intel
# ---------------------------------------------------------------------------

class UnifiedIntel(Base):
    """
    Consolidated intelligence item produced by the full collection → cluster →
    enrich → score → classify pipeline.

    cluster_key is the deduplication key (vendor:product:version:cve hash).
    used_in_marketing / used_at track Content_Service consumption.
    """

    __tablename__ = "unified_intel"
    __table_args__ = (
        sa.UniqueConstraint("cluster_key", name="uq_unified_intel_cluster_key"),
        sa.CheckConstraint(
            "risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH', 'CRITICAL')",
            name="ck_unified_intel_risk_level",
        ),
        sa.CheckConstraint(
            "classification IN ('PRODUCT_VULNERABILITY', 'COMPANY_BREACH', 'UNKNOWN')",
            name="ck_unified_intel_classification",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 100",
            name="ck_unified_intel_confidence_score",
        ),
        sa.CheckConstraint(
            "misinformation_status IS NULL OR misinformation_status IN "
            "('LEGITIMATE', 'MISINFORMATION', 'UNVERIFIED')",
            name="ck_unified_intel_misinformation_status",
        ),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    company_name: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    vendor_name: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    product_name: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    version_name: Mapped[str | None] = mapped_column(sa.String(255))
    primary_cve: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    content: Mapped[str | None] = mapped_column(sa.Text)

    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    frameworks: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    threat_score: Mapped[float | None] = mapped_column(sa.Float)
    compliance_score: Mapped[float | None] = mapped_column(sa.Float)
    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    severity: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    risk_level: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    classification_confidence: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    classification_reason: Mapped[str | None] = mapped_column(sa.Text)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)

    source_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    content_hash: Mapped[str | None] = mapped_column(sa.String(64), unique=True, index=True)
    cluster_key: Mapped[str] = mapped_column(sa.String(512), nullable=False, unique=True, index=True)

    llm_enriched: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    llm_summary: Mapped[str | None] = mapped_column(sa.Text)
    llm_model: Mapped[str | None] = mapped_column(sa.String(255))
    llm_provider: Mapped[str | None] = mapped_column(sa.String(64))
    llm_raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    misinformation_status: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    misinformation_confidence: Mapped[float | None] = mapped_column(sa.Float)
    suppressed_from_feed: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    # Marketing consumption tracking (task 2.3 / requirement 1.5, 6.1)
    used_in_marketing: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false(), index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    first_seen_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    latest_date: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# intel_posts  (social / researcher posts)
# ---------------------------------------------------------------------------

class IntelPost(Base):
    """
    Social and researcher posts from X/Twitter (via Nitter), Reddit,
    LinkedIn, and HackerNews.  Content-hash deduplication on every insert.
    """

    __tablename__ = "intel_posts"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_intel_posts_content_hash"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    platform: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.String(255))
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    search_query: Mapped[str | None] = mapped_column(sa.Text)
    matched_vendors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vuln_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_threat_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    has_poc: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    active_exploitation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    threat_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# vendor_advisory_intel
# ---------------------------------------------------------------------------

class VendorAdvisoryIntel(Base):
    """
    Vendor security advisories from MSRC, Cisco, Fortinet, Palo Alto, VMware, etc.
    """

    __tablename__ = "vendor_advisory_intel"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_vendor_advisory_intel_content_hash"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    vendor: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    matched_vendors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vuln_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_threat_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    severity: Mapped[str | None] = mapped_column(sa.String(50))

    has_poc: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    active_exploitation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    is_vendor_advisory: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.true()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    source_trust_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# vulnerability_intel
# ---------------------------------------------------------------------------

class VulnerabilityIntel(Base):
    """
    Vulnerability database intel from CVE Program, NVD, CISA KEV,
    GitHub PoC, Exploit-DB, and Metasploit.

    cve_id has a unique constraint for CVE-level deduplication (Req 2.6).
    content_hash unique constraint handles non-CVE deduplication.
    """

    __tablename__ = "vulnerability_intel"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_vulnerability_intel_content_hash"),
        sa.UniqueConstraint("cve_id", name="uq_vulnerability_intel_cve_id"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.String(255))
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    cve_id: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    cvss_score: Mapped[float | None] = mapped_column(sa.Float)
    severity: Mapped[str | None] = mapped_column(sa.String(50))

    matched_vendors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vuln_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_threat_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    in_cisa_kev: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    has_poc: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    has_exploit: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    active_exploitation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    source_trust_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# compliance_intel
# ---------------------------------------------------------------------------

class ComplianceIntel(Base):
    """
    Compliance intelligence: regulatory updates, framework changes, audit
    guidance, privacy rules, and AI governance from NIST, ISO, PCI DSS,
    GDPR, EU AI Act, etc.

    frameworks stored as JSONB (replaces the Text-serialised JSON list
    from the legacy SQLite model).
    """

    __tablename__ = "compliance_intel"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_compliance_intel_content_hash"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    organization: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    source_tier: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("2"), index=True
    )
    source_subtype: Mapped[str] = mapped_column(
        sa.String(30), nullable=False, server_default=sa.text("'regulatory'"), index=True
    )
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.String(255))
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    matched_compliance_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_privacy_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_audit_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_ai_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_framework_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    # JSONB — replaces legacy Text("[]") serialisation
    frameworks: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    framework_versions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    effective_dates: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    compliance_deadlines: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    impacted_controls: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    is_new_requirement: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    is_framework_update: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    source_trust_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# company_breach_intel
# ---------------------------------------------------------------------------

class CompanyBreachIntel(Base):
    """
    Company breach and ransomware incident news from Tier-1 outlets
    (KrebsOnSecurity, BleepingComputer, SecurityWeek, The Hacker News,
    Ransomware.live).
    """

    __tablename__ = "company_breach_intel"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_company_breach_intel_content_hash"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    source_tier: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("1"), index=True
    )
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.String(255))
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    affected_company: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    breach_type: Mapped[str | None] = mapped_column(sa.String(128), index=True)

    matched_breach_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vendors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vuln_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_threat_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    has_poc: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    active_exploitation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    is_ransomware: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    source_trust_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# research_blog_intel
# ---------------------------------------------------------------------------

class ResearchBlogIntel(Base):
    """
    High-trust researcher blog posts (Google Project Zero, Krebs, Unit42,
    DFIR Report, Rapid7, etc.).  Latest vulnerability research filtered by
    vendor + keyword and scored separately from social/advisory feeds.
    """

    __tablename__ = "research_blog_intel"
    __table_args__ = (
        sa.UniqueConstraint("content_hash", name="uq_research_blog_intel_content_hash"),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    source_id: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(sa.String(255))
    collection_method: Mapped[str | None] = mapped_column(sa.String(30))

    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=sa.text("''"))
    url: Mapped[str | None] = mapped_column(sa.Text)
    author: Mapped[str | None] = mapped_column(sa.String(255))
    published_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), index=True
    )

    matched_vendors: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_vuln_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    matched_threat_keywords: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )
    cves: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")
    )

    has_poc: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    active_exploitation: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    confidence_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    risk_level: Mapped[str] = mapped_column(
        sa.String(32), nullable=False, server_default=sa.text("'LOW'")
    )
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    score_reason: Mapped[str | None] = mapped_column(sa.Text)
    source_trust_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    keyword_match_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    recency_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )

    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# job_runs
# ---------------------------------------------------------------------------

class JobRun(Base):
    """
    Tracks execution state of each Celery pipeline task.  Written on task
    start and updated on completion / failure.  Displayed in the Security
    Dashboard jobs view.
    """

    __tablename__ = "job_runs"
    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_job_runs_status",
        ),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    task_name: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    error_message: Mapped[str | None] = mapped_column(sa.Text)

    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


# ---------------------------------------------------------------------------
# osint_scan_results
# ---------------------------------------------------------------------------

class OsintScanResult(Base):
    """
    Persisted results from the three OSINT investigation endpoints:
    company-scan, employee-leak, and infra-recon.

    query_params and results are JSONB for flexible tool-specific payloads.
    initiated_by FK → users (nullable on user deletion).
    """

    __tablename__ = "osint_scan_results"
    __table_args__ = (
        sa.CheckConstraint(
            "scan_type IN ('company', 'employee', 'infra')",
            name="ck_osint_scan_results_scan_type",
        ),
        sa.CheckConstraint(
            "threat_score >= 0 AND threat_score <= 100",
            name="ck_osint_scan_results_threat_score",
        ),
    )

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    scan_type: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    query_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    results: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    threat_score: Mapped[float] = mapped_column(
        sa.Float, nullable=False, server_default=sa.text("0")
    )
    initiated_by: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True
    )

    # relationship back to User
    initiator: Mapped["User | None"] = relationship(back_populates="osint_scans")


# ---------------------------------------------------------------------------
# __all__  — export every model for easy star-import in env.py
# ---------------------------------------------------------------------------

__all__ = [
    "User",
    "UnifiedIntel",
    "IntelPost",
    "VendorAdvisoryIntel",
    "VulnerabilityIntel",
    "ComplianceIntel",
    "CompanyBreachIntel",
    "ResearchBlogIntel",
    "JobRun",
    "OsintScanResult",
]
