"""Create initial Intelligence_Service schema

Revision ID: 001
Revises:
Create Date: 2026-06-23 00:00:00.000000

Requirements: 1.4, 2.3, 2.6, 3.1, 3.2, 3.3
"""

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(r'''
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    CREATE TABLE users (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        email varchar(320) NOT NULL UNIQUE,
        password_hash varchar(255) NOT NULL,
        role varchar(32) NOT NULL CHECK (role IN ('security_team', 'marketing_team')),
        display_name varchar(255),
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE unified_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        company_name varchar(255), vendor_name varchar(255), product_name varchar(255), version_name varchar(255),
        primary_cve varchar(32),
        latest_date timestamptz NOT NULL,
        first_seen_at timestamptz,
        published_at timestamptz,
        title text NOT NULL, summary text, content text,
        cves jsonb NOT NULL DEFAULT '[]'::jsonb,
        frameworks jsonb NOT NULL DEFAULT '[]'::jsonb,
        threat_score double precision, compliance_score double precision,
        confidence_score double precision NOT NULL DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),
        severity varchar(32),
        risk_level varchar(32) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH', 'CRITICAL')),
        classification varchar(64) NOT NULL CHECK (classification IN ('PRODUCT_VULNERABILITY', 'COMPANY_BREACH', 'UNKNOWN')),
        classification_confidence double precision NOT NULL DEFAULT 0 CHECK (classification_confidence >= 0 AND classification_confidence <= 99),
        classification_reason text,
        score_breakdown jsonb NOT NULL DEFAULT '{}'::jsonb,
        score_reason text,
        source_count integer NOT NULL DEFAULT 0,
        source_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
        llm_summary text, llm_model varchar(255), llm_enriched boolean NOT NULL DEFAULT false,
        llm_provider varchar(64), llm_raw_response jsonb,
        misinformation_status varchar(32) CHECK (misinformation_status IN ('LEGITIMATE', 'MISINFORMATION', 'UNVERIFIED')),
        misinformation_confidence double precision,
        suppressed_from_feed boolean NOT NULL DEFAULT false,
        content_hash varchar(64) UNIQUE,
        cluster_key varchar(512) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE intel_posts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        platform varchar(64) NOT NULL, source_id varchar(255) NOT NULL, source_name varchar(255),
        title text NOT NULL, content text NOT NULL, url text, author varchar(255), published_at timestamptz,
        matched_vendors jsonb NOT NULL DEFAULT '[]'::jsonb,
        cves jsonb NOT NULL DEFAULT '[]'::jsonb,
        confidence_score double precision NOT NULL DEFAULT 0,
        risk_level varchar(32) NOT NULL,
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE vendor_advisory_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id varchar(255) NOT NULL, vendor varchar(255), title text NOT NULL, content text NOT NULL,
        cves jsonb NOT NULL DEFAULT '[]'::jsonb,
        confidence_score double precision NOT NULL DEFAULT 0,
        risk_level varchar(32) NOT NULL,
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE vulnerability_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id varchar(255) NOT NULL, cve_id varchar(32) NOT NULL UNIQUE, cvss_score double precision,
        in_cisa_kev boolean NOT NULL DEFAULT false, has_poc boolean NOT NULL DEFAULT false, has_exploit boolean NOT NULL DEFAULT false,
        confidence_score double precision NOT NULL DEFAULT 0 CHECK (confidence_score >= 0 AND confidence_score <= 100),
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE compliance_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id varchar(255) NOT NULL, organization varchar(255), frameworks jsonb NOT NULL DEFAULT '[]'::jsonb,
        confidence_score double precision NOT NULL DEFAULT 0,
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE company_breach_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id varchar(255) NOT NULL, affected_company varchar(255) NOT NULL, breach_type varchar(128), is_ransomware boolean NOT NULL DEFAULT false,
        confidence_score double precision NOT NULL DEFAULT 0,
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE research_blog_intel (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        source_id varchar(255) NOT NULL, source_name varchar(255), title text NOT NULL,
        cves jsonb NOT NULL DEFAULT '[]'::jsonb,
        confidence_score double precision NOT NULL DEFAULT 0,
        content_hash varchar(64) NOT NULL UNIQUE,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE TABLE job_runs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        task_name varchar(255) NOT NULL, status varchar(32) NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
        retry_count integer NOT NULL DEFAULT 0, error_message text,
        started_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz, next_run_at timestamptz
    );

    CREATE TABLE osint_scan_results (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        scan_type varchar(32) NOT NULL CHECK (scan_type IN ('company', 'employee', 'infra')),
        query_params jsonb NOT NULL DEFAULT '{}'::jsonb,
        results jsonb NOT NULL DEFAULT '{}'::jsonb,
        threat_score double precision NOT NULL DEFAULT 0 CHECK (threat_score >= 0 AND threat_score <= 100),
        initiated_by uuid REFERENCES users(id) ON DELETE SET NULL,
        created_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE INDEX ix_users_role ON users(role);
    CREATE INDEX ix_unified_intel_classification ON unified_intel(classification);
    CREATE INDEX ix_unified_intel_severity ON unified_intel(severity);
    CREATE INDEX ix_unified_intel_risk_level ON unified_intel(risk_level);
    CREATE INDEX ix_unified_intel_confidence_score ON unified_intel(confidence_score);
    CREATE INDEX ix_unified_intel_latest_date ON unified_intel(latest_date);
    CREATE INDEX ix_unified_intel_published_at ON unified_intel(published_at);
    CREATE INDEX ix_unified_intel_primary_cve ON unified_intel(primary_cve);
    CREATE INDEX ix_unified_intel_content_hash ON unified_intel(content_hash);
    CREATE INDEX ix_unified_intel_misinformation_status ON unified_intel(misinformation_status);
    CREATE INDEX ix_unified_intel_vendor_product ON unified_intel(vendor_name, product_name);
    CREATE INDEX ix_unified_intel_cves_gin ON unified_intel USING gin(cves);
    CREATE INDEX ix_unified_intel_frameworks_gin ON unified_intel USING gin(frameworks);
    CREATE INDEX ix_unified_intel_source_refs_gin ON unified_intel USING gin(source_refs);
    CREATE INDEX ix_intel_posts_platform ON intel_posts(platform);
    CREATE INDEX ix_intel_posts_source_id ON intel_posts(source_id);
    CREATE INDEX ix_intel_posts_published_at ON intel_posts(published_at);
    CREATE INDEX ix_intel_posts_cves_gin ON intel_posts USING gin(cves);
    CREATE INDEX ix_vendor_advisory_intel_vendor ON vendor_advisory_intel(vendor);
    CREATE INDEX ix_vendor_advisory_intel_source_id ON vendor_advisory_intel(source_id);
    CREATE INDEX ix_vendor_advisory_intel_cves_gin ON vendor_advisory_intel USING gin(cves);
    CREATE INDEX ix_vulnerability_intel_source_id ON vulnerability_intel(source_id);
    CREATE INDEX ix_vulnerability_intel_cve_id ON vulnerability_intel(cve_id);
    CREATE INDEX ix_vulnerability_intel_in_cisa_kev ON vulnerability_intel(in_cisa_kev);
    CREATE INDEX ix_compliance_intel_source_id ON compliance_intel(source_id);
    CREATE INDEX ix_compliance_intel_organization ON compliance_intel(organization);
    CREATE INDEX ix_compliance_intel_frameworks_gin ON compliance_intel USING gin(frameworks);
    CREATE INDEX ix_company_breach_intel_source_id ON company_breach_intel(source_id);
    CREATE INDEX ix_company_breach_intel_affected_company ON company_breach_intel(affected_company);
    CREATE INDEX ix_research_blog_intel_source_id ON research_blog_intel(source_id);
    CREATE INDEX ix_research_blog_intel_cves_gin ON research_blog_intel USING gin(cves);
    CREATE INDEX ix_job_runs_task_name ON job_runs(task_name);
    CREATE INDEX ix_job_runs_status ON job_runs(status);
    CREATE INDEX ix_job_runs_started_at ON job_runs(started_at);
    CREATE INDEX ix_osint_scan_results_scan_type ON osint_scan_results(scan_type);
    CREATE INDEX ix_osint_scan_results_initiated_by ON osint_scan_results(initiated_by);
    CREATE INDEX ix_osint_scan_results_created_at ON osint_scan_results(created_at);
    ''')


def downgrade() -> None:
    op.execute(r'''
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
    ''')
