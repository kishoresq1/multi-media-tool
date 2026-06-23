"""Create initial Intelligence_Service tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

Requirements: 1.4, 2.3, 2.6, 3.1, 3.2, 3.3

Creates the following tables:
  - users                   (JWT auth + RBAC)
  - unified_intel           (canonical intel items; cluster_key UK; used_in_marketing)
  - intel_posts             (social/researcher posts; content_hash UK)
  - vendor_advisory_intel   (vendor advisories; content_hash UK)
  - vulnerability_intel     (CVE/NVD/KEV records; cve_id UK + content_hash UK)
  - compliance_intel        (regulatory/framework updates; content_hash UK; frameworks JSONB)
  - company_breach_intel    (breach/ransomware news; content_hash UK)
  - research_blog_intel     (researcher blogs; content_hash UK)
  - job_runs                (Celery task execution log)
  - osint_scan_results      (investigation tool results; initiated_by FK → users)
"""

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- ── Extensions ────────────────────────────────────────────────────────────
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        -- ── users ──────────────────────────────────────────────────────────────────
        -- Holds both security_team and marketing_team members.
        -- JWT tokens carry the role claim; Intelligence_Service is the only issuer.
        CREATE TABLE users (
            id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            email         varchar(320) NOT NULL,
            password_hash varchar(255) NOT NULL,
            role          varchar(32)  NOT NULL
                              CHECK (role IN ('security_team', 'marketing_team')),
            display_name  varchar(255),
            created_at    timestamptz  NOT NULL DEFAULT now(),
            updated_at    timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_users_email UNIQUE (email)
        );

        CREATE INDEX ix_users_role ON users (role);
        """
    )

    op.execute(
        """
        -- ── unified_intel ──────────────────────────────────────────────────────────
        -- Central output of the collect → cluster → enrich → score → classify pipeline.
        -- cluster_key UK: deduplication by vendor:product:version:cve composite.
        -- used_in_marketing / used_at: track Content_Service consumption (Req 1.5, 6.1).
        -- Index on used_in_marketing supports the GET /feed marketing queue query.
        CREATE TABLE unified_intel (
            id                       uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
            company_name             varchar(255),
            vendor_name              varchar(255),
            product_name             varchar(255),
            version_name             varchar(255),
            primary_cve              varchar(32),
            title                    text          NOT NULL,
            summary                  text,
            content                  text,
            cves                     jsonb         NOT NULL DEFAULT '[]'::jsonb,
            frameworks               jsonb         NOT NULL DEFAULT '[]'::jsonb,
            threat_score             double precision,
            compliance_score         double precision,
            confidence_score         double precision NOT NULL DEFAULT 0
                                         CHECK (confidence_score >= 0 AND confidence_score <= 100),
            severity                 varchar(32),
            risk_level               varchar(32)   NOT NULL
                                         CHECK (risk_level IN ('LOW','MEDIUM','HIGH','VERY_HIGH','CRITICAL')),
            classification           varchar(64)   NOT NULL
                                         CHECK (classification IN ('PRODUCT_VULNERABILITY','COMPANY_BREACH','UNKNOWN')),
            classification_confidence double precision NOT NULL DEFAULT 0
                                         CHECK (classification_confidence >= 0 AND classification_confidence <= 99),
            classification_reason    text,
            score_breakdown          jsonb         NOT NULL DEFAULT '{}'::jsonb,
            score_reason             text,
            source_count             integer       NOT NULL DEFAULT 0,
            source_refs              jsonb         NOT NULL DEFAULT '[]'::jsonb,
            llm_summary              text,
            llm_model                varchar(255),
            llm_enriched             boolean       NOT NULL DEFAULT false,
            llm_provider             varchar(64),
            llm_raw_response         jsonb,
            misinformation_status    varchar(32)
                                         CHECK (misinformation_status IS NULL
                                                OR misinformation_status IN
                                                   ('LEGITIMATE','MISINFORMATION','UNVERIFIED')),
            misinformation_confidence double precision,
            suppressed_from_feed     boolean       NOT NULL DEFAULT false,
            used_in_marketing        boolean       NOT NULL DEFAULT false,
            used_at                  timestamptz,
            content_hash             varchar(64)   UNIQUE,
            cluster_key              varchar(512)  NOT NULL,
            first_seen_at            timestamptz,
            latest_date              timestamptz,
            published_at             timestamptz,
            created_at               timestamptz   NOT NULL DEFAULT now(),
            updated_at               timestamptz   NOT NULL DEFAULT now(),
            CONSTRAINT uq_unified_intel_cluster_key UNIQUE (cluster_key)
        );

        CREATE INDEX ix_unified_intel_classification      ON unified_intel (classification);
        CREATE INDEX ix_unified_intel_severity            ON unified_intel (severity);
        CREATE INDEX ix_unified_intel_risk_level          ON unified_intel (risk_level);
        CREATE INDEX ix_unified_intel_confidence_score    ON unified_intel (confidence_score);
        CREATE INDEX ix_unified_intel_latest_date         ON unified_intel (latest_date);
        CREATE INDEX ix_unified_intel_published_at        ON unified_intel (published_at);
        CREATE INDEX ix_unified_intel_primary_cve         ON unified_intel (primary_cve);
        CREATE INDEX ix_unified_intel_vendor_name         ON unified_intel (vendor_name);
        CREATE INDEX ix_unified_intel_product_name        ON unified_intel (product_name);
        CREATE INDEX ix_unified_intel_company_name        ON unified_intel (company_name);
        CREATE INDEX ix_unified_intel_used_in_marketing   ON unified_intel (used_in_marketing);
        CREATE INDEX ix_unified_intel_misinformation      ON unified_intel (misinformation_status);
        CREATE INDEX ix_unified_intel_vendor_product      ON unified_intel (vendor_name, product_name);
        CREATE INDEX ix_unified_intel_cves_gin            ON unified_intel USING gin (cves);
        CREATE INDEX ix_unified_intel_frameworks_gin      ON unified_intel USING gin (frameworks);
        CREATE INDEX ix_unified_intel_source_refs_gin     ON unified_intel USING gin (source_refs);
        """
    )

    op.execute(
        """
        -- ── intel_posts ────────────────────────────────────────────────────────────
        -- Social and researcher posts (X/Nitter, Reddit, LinkedIn, HackerNews).
        -- content_hash UK: SHA-256 of normalised title+content prevents duplicates.
        -- All JSON-in-text columns from the legacy SQLite model replaced with JSONB.
        CREATE TABLE intel_posts (
            id                     uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            platform               varchar(64)  NOT NULL,
            source_id              varchar(255) NOT NULL,
            source_name            varchar(255),
            collection_method      varchar(30),
            title                  text         NOT NULL,
            content                text         NOT NULL DEFAULT '',
            url                    text,
            author                 varchar(255),
            published_at           timestamptz,
            search_query           text,
            matched_vendors        jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vuln_keywords  jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_threat_keywords jsonb       NOT NULL DEFAULT '[]'::jsonb,
            cves                   jsonb        NOT NULL DEFAULT '[]'::jsonb,
            has_poc                boolean      NOT NULL DEFAULT false,
            active_exploitation    boolean      NOT NULL DEFAULT false,
            confidence_score       double precision NOT NULL DEFAULT 0,
            risk_level             varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown        jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason           text,
            keyword_match_score    double precision NOT NULL DEFAULT 0,
            recency_score          double precision NOT NULL DEFAULT 0,
            threat_score           double precision NOT NULL DEFAULT 0,
            content_hash           varchar(64)  NOT NULL,
            created_at             timestamptz  NOT NULL DEFAULT now(),
            updated_at             timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_intel_posts_content_hash UNIQUE (content_hash)
        );

        CREATE INDEX ix_intel_posts_platform     ON intel_posts (platform);
        CREATE INDEX ix_intel_posts_source_id    ON intel_posts (source_id);
        CREATE INDEX ix_intel_posts_published_at ON intel_posts (published_at);
        CREATE INDEX ix_intel_posts_cves_gin      ON intel_posts USING gin (cves);
        """
    )

    op.execute(
        """
        -- ── vendor_advisory_intel ──────────────────────────────────────────────────
        -- Vendor security advisories (MSRC, Cisco, Fortinet, Palo Alto, VMware …).
        CREATE TABLE vendor_advisory_intel (
            id                     uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id              varchar(255) NOT NULL,
            source_name            varchar(255),
            vendor                 varchar(255),
            collection_method      varchar(30),
            title                  text         NOT NULL,
            content                text         NOT NULL DEFAULT '',
            url                    text,
            published_at           timestamptz,
            matched_vendors        jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vuln_keywords  jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_threat_keywords jsonb       NOT NULL DEFAULT '[]'::jsonb,
            cves                   jsonb        NOT NULL DEFAULT '[]'::jsonb,
            severity               varchar(50),
            has_poc                boolean      NOT NULL DEFAULT false,
            active_exploitation    boolean      NOT NULL DEFAULT false,
            is_vendor_advisory     boolean      NOT NULL DEFAULT true,
            confidence_score       double precision NOT NULL DEFAULT 0,
            risk_level             varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown        jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason           text,
            source_trust_score     double precision NOT NULL DEFAULT 0,
            keyword_match_score    double precision NOT NULL DEFAULT 0,
            recency_score          double precision NOT NULL DEFAULT 0,
            content_hash           varchar(64)  NOT NULL,
            created_at             timestamptz  NOT NULL DEFAULT now(),
            updated_at             timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_vendor_advisory_intel_content_hash UNIQUE (content_hash)
        );

        CREATE INDEX ix_vendor_advisory_intel_source_id    ON vendor_advisory_intel (source_id);
        CREATE INDEX ix_vendor_advisory_intel_vendor       ON vendor_advisory_intel (vendor);
        CREATE INDEX ix_vendor_advisory_intel_published_at ON vendor_advisory_intel (published_at);
        CREATE INDEX ix_vendor_advisory_intel_cves_gin     ON vendor_advisory_intel USING gin (cves);
        """
    )

    op.execute(
        """
        -- ── vulnerability_intel ────────────────────────────────────────────────────
        -- CVE Program, NVD, CISA KEV, GitHub PoC, Exploit-DB, Metasploit records.
        -- cve_id UNIQUE: one row per CVE — prevents duplicate KEV/NVD inserts (Req 2.6).
        -- content_hash UNIQUE: deduplication for non-CVE records.
        -- Both constraints are NULL-safe: a NULL cve_id does NOT violate the unique
        -- constraint (PostgreSQL allows multiple NULLs in a unique column).
        CREATE TABLE vulnerability_intel (
            id                      uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id               varchar(255) NOT NULL,
            source_name             varchar(255),
            collection_method       varchar(30),
            title                   text         NOT NULL,
            content                 text         NOT NULL DEFAULT '',
            url                     text,
            author                  varchar(255),
            published_at            timestamptz,
            cve_id                  varchar(32),
            cvss_score              double precision,
            severity                varchar(50),
            matched_vendors         jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vuln_keywords   jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_threat_keywords jsonb        NOT NULL DEFAULT '[]'::jsonb,
            cves                    jsonb        NOT NULL DEFAULT '[]'::jsonb,
            in_cisa_kev             boolean      NOT NULL DEFAULT false,
            has_poc                 boolean      NOT NULL DEFAULT false,
            has_exploit             boolean      NOT NULL DEFAULT false,
            active_exploitation     boolean      NOT NULL DEFAULT false,
            confidence_score        double precision NOT NULL DEFAULT 0
                                        CHECK (confidence_score >= 0 AND confidence_score <= 100),
            risk_level              varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown         jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason            text,
            source_trust_score      double precision NOT NULL DEFAULT 0,
            keyword_match_score     double precision NOT NULL DEFAULT 0,
            recency_score           double precision NOT NULL DEFAULT 0,
            content_hash            varchar(64)  NOT NULL,
            created_at              timestamptz  NOT NULL DEFAULT now(),
            updated_at              timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_vulnerability_intel_content_hash UNIQUE (content_hash),
            CONSTRAINT uq_vulnerability_intel_cve_id       UNIQUE (cve_id)
        );

        CREATE INDEX ix_vulnerability_intel_source_id    ON vulnerability_intel (source_id);
        CREATE INDEX ix_vulnerability_intel_cve_id       ON vulnerability_intel (cve_id);
        CREATE INDEX ix_vulnerability_intel_in_cisa_kev  ON vulnerability_intel (in_cisa_kev);
        CREATE INDEX ix_vulnerability_intel_published_at ON vulnerability_intel (published_at);
        CREATE INDEX ix_vulnerability_intel_cves_gin     ON vulnerability_intel USING gin (cves);
        """
    )

    op.execute(
        """
        -- ── compliance_intel ───────────────────────────────────────────────────────
        -- Regulatory updates, framework changes, audit guidance from NIST, ISO,
        -- PCI DSS, GDPR, EU AI Act, and other standards bodies.
        -- frameworks JSONB replaces the legacy Text('[]') serialisation (Req 3.2).
        CREATE TABLE compliance_intel (
            id                        uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id                 varchar(255) NOT NULL,
            source_name               varchar(255),
            organization              varchar(255),
            source_tier               integer      NOT NULL DEFAULT 2,
            source_subtype            varchar(30)  NOT NULL DEFAULT 'regulatory',
            collection_method         varchar(30),
            title                     text         NOT NULL,
            content                   text         NOT NULL DEFAULT '',
            url                       text,
            author                    varchar(255),
            published_at              timestamptz,
            matched_compliance_keywords jsonb      NOT NULL DEFAULT '[]'::jsonb,
            matched_privacy_keywords  jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_audit_keywords    jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_ai_keywords       jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_framework_keywords jsonb       NOT NULL DEFAULT '[]'::jsonb,
            frameworks                jsonb        NOT NULL DEFAULT '[]'::jsonb,
            framework_versions        jsonb        NOT NULL DEFAULT '[]'::jsonb,
            effective_dates           jsonb        NOT NULL DEFAULT '[]'::jsonb,
            compliance_deadlines      jsonb        NOT NULL DEFAULT '[]'::jsonb,
            impacted_controls         jsonb        NOT NULL DEFAULT '[]'::jsonb,
            is_new_requirement        boolean      NOT NULL DEFAULT false,
            is_framework_update       boolean      NOT NULL DEFAULT false,
            confidence_score          double precision NOT NULL DEFAULT 0,
            risk_level                varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown           jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason              text,
            source_trust_score        double precision NOT NULL DEFAULT 0,
            keyword_match_score       double precision NOT NULL DEFAULT 0,
            recency_score             double precision NOT NULL DEFAULT 0,
            content_hash              varchar(64)  NOT NULL,
            created_at                timestamptz  NOT NULL DEFAULT now(),
            updated_at                timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_compliance_intel_content_hash UNIQUE (content_hash)
        );

        CREATE INDEX ix_compliance_intel_source_id      ON compliance_intel (source_id);
        CREATE INDEX ix_compliance_intel_organization   ON compliance_intel (organization);
        CREATE INDEX ix_compliance_intel_source_tier    ON compliance_intel (source_tier);
        CREATE INDEX ix_compliance_intel_source_subtype ON compliance_intel (source_subtype);
        CREATE INDEX ix_compliance_intel_published_at   ON compliance_intel (published_at);
        CREATE INDEX ix_compliance_intel_frameworks_gin ON compliance_intel USING gin (frameworks);
        """
    )

    op.execute(
        """
        -- ── company_breach_intel ───────────────────────────────────────────────────
        -- Breach and ransomware incident news from Tier-1 security outlets.
        CREATE TABLE company_breach_intel (
            id                       uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id                varchar(255) NOT NULL,
            source_name              varchar(255),
            source_tier              integer      NOT NULL DEFAULT 1,
            collection_method        varchar(30),
            title                    text         NOT NULL,
            content                  text         NOT NULL DEFAULT '',
            url                      text,
            author                   varchar(255),
            published_at             timestamptz,
            affected_company         varchar(255),
            breach_type              varchar(128),
            matched_breach_keywords  jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vendors          jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vuln_keywords    jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_threat_keywords  jsonb        NOT NULL DEFAULT '[]'::jsonb,
            cves                     jsonb        NOT NULL DEFAULT '[]'::jsonb,
            has_poc                  boolean      NOT NULL DEFAULT false,
            active_exploitation      boolean      NOT NULL DEFAULT false,
            is_ransomware            boolean      NOT NULL DEFAULT false,
            confidence_score         double precision NOT NULL DEFAULT 0,
            risk_level               varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown          jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason             text,
            source_trust_score       double precision NOT NULL DEFAULT 0,
            keyword_match_score      double precision NOT NULL DEFAULT 0,
            recency_score            double precision NOT NULL DEFAULT 0,
            content_hash             varchar(64)  NOT NULL,
            created_at               timestamptz  NOT NULL DEFAULT now(),
            updated_at               timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_company_breach_intel_content_hash UNIQUE (content_hash)
        );

        CREATE INDEX ix_company_breach_intel_source_id       ON company_breach_intel (source_id);
        CREATE INDEX ix_company_breach_intel_source_tier     ON company_breach_intel (source_tier);
        CREATE INDEX ix_company_breach_intel_affected_company ON company_breach_intel (affected_company);
        CREATE INDEX ix_company_breach_intel_breach_type     ON company_breach_intel (breach_type);
        CREATE INDEX ix_company_breach_intel_published_at    ON company_breach_intel (published_at);

        -- ── research_blog_intel ────────────────────────────────────────────────────
        -- High-trust researcher blogs (Project Zero, Krebs, Unit42, DFIR Report …).
        CREATE TABLE research_blog_intel (
            id                      uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id               varchar(255) NOT NULL,
            source_name             varchar(255),
            collection_method       varchar(30),
            title                   text         NOT NULL,
            content                 text         NOT NULL DEFAULT '',
            url                     text,
            author                  varchar(255),
            published_at            timestamptz,
            matched_vendors         jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_vuln_keywords   jsonb        NOT NULL DEFAULT '[]'::jsonb,
            matched_threat_keywords jsonb        NOT NULL DEFAULT '[]'::jsonb,
            cves                    jsonb        NOT NULL DEFAULT '[]'::jsonb,
            has_poc                 boolean      NOT NULL DEFAULT false,
            active_exploitation     boolean      NOT NULL DEFAULT false,
            confidence_score        double precision NOT NULL DEFAULT 0,
            risk_level              varchar(32)  NOT NULL DEFAULT 'LOW',
            score_breakdown         jsonb        NOT NULL DEFAULT '{}'::jsonb,
            score_reason            text,
            source_trust_score      double precision NOT NULL DEFAULT 0,
            keyword_match_score     double precision NOT NULL DEFAULT 0,
            recency_score           double precision NOT NULL DEFAULT 0,
            content_hash            varchar(64)  NOT NULL,
            created_at              timestamptz  NOT NULL DEFAULT now(),
            updated_at              timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_research_blog_intel_content_hash UNIQUE (content_hash)
        );

        CREATE INDEX ix_research_blog_intel_source_id    ON research_blog_intel (source_id);
        CREATE INDEX ix_research_blog_intel_published_at ON research_blog_intel (published_at);
        CREATE INDEX ix_research_blog_intel_cves_gin     ON research_blog_intel USING gin (cves);
        """
    )

    op.execute(
        """
        -- ── job_runs ───────────────────────────────────────────────────────────────
        -- Tracks Celery pipeline task lifecycle (queued → running → completed/failed).
        -- Displayed in the Security Dashboard jobs view (Req 11.4).
        CREATE TABLE job_runs (
            id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            task_name     varchar(255) NOT NULL,
            status        varchar(32)  NOT NULL
                              CHECK (status IN ('queued', 'running', 'completed', 'failed')),
            retry_count   integer      NOT NULL DEFAULT 0,
            error_message text,
            started_at    timestamptz  NOT NULL DEFAULT now(),
            completed_at  timestamptz,
            next_run_at   timestamptz
        );

        CREATE INDEX ix_job_runs_task_name  ON job_runs (task_name);
        CREATE INDEX ix_job_runs_status     ON job_runs (status);
        CREATE INDEX ix_job_runs_started_at ON job_runs (started_at);

        -- ── osint_scan_results ─────────────────────────────────────────────────────
        -- Persisted results from the three OSINT investigation endpoints.
        -- initiated_by FK → users; SET NULL on user deletion preserves audit trail.
        CREATE TABLE osint_scan_results (
            id           uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
            scan_type    varchar(32)  NOT NULL
                             CHECK (scan_type IN ('company', 'employee', 'infra')),
            query_params jsonb        NOT NULL DEFAULT '{}'::jsonb,
            results      jsonb        NOT NULL DEFAULT '{}'::jsonb,
            threat_score double precision NOT NULL DEFAULT 0
                             CHECK (threat_score >= 0 AND threat_score <= 100),
            initiated_by uuid         REFERENCES users (id) ON DELETE SET NULL,
            created_at   timestamptz  NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_osint_scan_results_scan_type    ON osint_scan_results (scan_type);
        CREATE INDEX ix_osint_scan_results_initiated_by ON osint_scan_results (initiated_by);
        CREATE INDEX ix_osint_scan_results_created_at   ON osint_scan_results (created_at);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS osint_scan_results;
        DROP TABLE IF EXISTS job_runs;
        DROP TABLE IF EXISTS research_blog_intel;
        DROP TABLE IF EXISTS company_breach_intel;
        DROP TABLE IF EXISTS compliance_intel;
        DROP TABLE IF EXISTS vulnerability_intel;
        DROP TABLE IF EXISTS vendor_advisory_intel;
        DROP TABLE IF EXISTS intel_posts;
        DROP TABLE IF EXISTS unified_intel;
        DROP TABLE IF EXISTS users;
        """
    )
