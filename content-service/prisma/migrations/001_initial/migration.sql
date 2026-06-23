-- Migration: 001_initial
-- Content_Service tables for the Unified Multimedia Platform
-- PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE "ContentAssetType" AS ENUM (
        'email',
        'hyperframe',
        'video',
        'linkedin_post',
        'slack_msg',
        'teams_msg'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE "ContentAssetStatus" AS ENUM (
        'pending_review',
        'approved',
        'rejected',
        'published'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE "CampaignStatus" AS ENUM (
        'draft',
        'approved',
        'sent'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE "ApprovalHistoryAction" AS ENUM (
        'submitted',
        'approved',
        'rejected',
        'edited'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS content_assets (
    id                   UUID                 NOT NULL DEFAULT gen_random_uuid(),
    asset_type           "ContentAssetType"   NOT NULL,
    intel_id             UUID,
    status               "ContentAssetStatus" NOT NULL DEFAULT 'pending_review',
    ai_generated_content JSONB,
    human_edited_content JSONB,
    reviewer_notes       VARCHAR(2000),
    reviewed_by          UUID,
    reviewed_at          TIMESTAMPTZ,
    edited_at            TIMESTAMPTZ,
    file_path            VARCHAR,
    mime_type            VARCHAR,
    created_by           UUID,
    created_at           TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ          NOT NULL DEFAULT NOW(),
    CONSTRAINT content_assets_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_content_assets_status_created_at
    ON content_assets (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_content_assets_asset_type
    ON content_assets (asset_type);

CREATE INDEX IF NOT EXISTS idx_content_assets_intel_id
    ON content_assets (intel_id);

CREATE INDEX IF NOT EXISTS idx_content_assets_created_by
    ON content_assets (created_by);

CREATE INDEX IF NOT EXISTS idx_content_assets_reviewed_by
    ON content_assets (reviewed_by);

CREATE TABLE IF NOT EXISTS campaigns (
    id             UUID             NOT NULL DEFAULT gen_random_uuid(),
    asset_id       UUID,
    intel_id       UUID,
    intel_title    VARCHAR,
    campaign_data  JSONB,
    recipients     JSONB,
    status         "CampaignStatus" NOT NULL DEFAULT 'draft',
    sent_at        TIMESTAMPTZ,
    email_delivery JSONB,
    created_at     TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    CONSTRAINT campaigns_pkey PRIMARY KEY (id),
    CONSTRAINT campaigns_asset_id_fkey FOREIGN KEY (asset_id)
        REFERENCES content_assets (id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_campaigns_asset_id
    ON campaigns (asset_id);

CREATE INDEX IF NOT EXISTS idx_campaigns_intel_id
    ON campaigns (intel_id);

CREATE INDEX IF NOT EXISTS idx_campaigns_status_created_at
    ON campaigns (status, created_at DESC);

CREATE TABLE IF NOT EXISTS subscribers (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    email       VARCHAR     NOT NULL,
    name        VARCHAR,
    company     VARCHAR,
    active      BOOLEAN     NOT NULL DEFAULT TRUE,
    preferences JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT subscribers_pkey PRIMARY KEY (id),
    CONSTRAINT subscribers_email_key UNIQUE (email)
);

CREATE INDEX IF NOT EXISTS idx_subscribers_active_created_at
    ON subscribers (active, created_at DESC);

CREATE TABLE IF NOT EXISTS linkedin_oauth_tokens (
    id            UUID        NOT NULL DEFAULT gen_random_uuid(),
    member_sub    VARCHAR     NOT NULL,
    member_urn    VARCHAR     NOT NULL,
    display_name  VARCHAR     NOT NULL,
    access_token  TEXT        NOT NULL,
    refresh_token TEXT,
    expires_at    TIMESTAMPTZ NOT NULL,
    scopes        VARCHAR,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT linkedin_oauth_tokens_pkey PRIMARY KEY (id),
    CONSTRAINT linkedin_oauth_tokens_member_sub_key UNIQUE (member_sub)
);

CREATE TABLE IF NOT EXISTS approval_queue_history (
    id         UUID                    NOT NULL DEFAULT gen_random_uuid(),
    asset_id   UUID                    NOT NULL,
    action     "ApprovalHistoryAction" NOT NULL,
    actor_id   UUID,
    notes      TEXT,
    created_at TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
    CONSTRAINT approval_queue_history_pkey PRIMARY KEY (id),
    CONSTRAINT approval_queue_history_asset_id_fkey FOREIGN KEY (asset_id)
        REFERENCES content_assets (id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_approval_queue_history_asset_created_at
    ON approval_queue_history (asset_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_approval_queue_history_action_created_at
    ON approval_queue_history (action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_approval_queue_history_actor_id
    ON approval_queue_history (actor_id);