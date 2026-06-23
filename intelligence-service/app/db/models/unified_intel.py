"""ORM model for the unified_intel table."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UnifiedIntel(Base):
    """Canonical intelligence item produced by the unified pipeline."""

    __tablename__ = "unified_intel"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(sa.Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    content: Mapped[str | None] = mapped_column(sa.Text)

    classification: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    severity: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    risk_level: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    threat_score: Mapped[float | None] = mapped_column(sa.Float)
    compliance_score: Mapped[float | None] = mapped_column(sa.Float)
    classification_confidence: Mapped[float] = mapped_column(sa.Float, nullable=False, server_default=sa.text("0"))
    classification_reason: Mapped[str | None] = mapped_column(sa.Text)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))
    score_reason: Mapped[str | None] = mapped_column(sa.Text)

    vendor_name: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    product_name: Mapped[str | None] = mapped_column(sa.String(255), index=True)
    version_name: Mapped[str | None] = mapped_column(sa.String(255))
    primary_cve: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    company_name: Mapped[str | None] = mapped_column(sa.String(255))
    cves: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
    frameworks: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))

    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
    source_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("0"))
    content_hash: Mapped[str | None] = mapped_column(sa.String(64), unique=True, index=True)
    cluster_key: Mapped[str] = mapped_column(sa.String(512), nullable=False, unique=True, index=True)

    llm_enriched: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    llm_summary: Mapped[str | None] = mapped_column(sa.Text)
    llm_model: Mapped[str | None] = mapped_column(sa.String(255))
    llm_provider: Mapped[str | None] = mapped_column(sa.String(64))
    llm_raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    misinformation_status: Mapped[str | None] = mapped_column(sa.String(32), index=True)
    misinformation_confidence: Mapped[float | None] = mapped_column(sa.Float)
    suppressed_from_feed: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())

    used_in_marketing: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
        index=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    first_seen_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    latest_date: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
