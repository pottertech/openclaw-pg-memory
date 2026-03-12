-- PostgreSQL pg-memory Retention System Schema v3.2.0
-- Migration from v3.1.2
-- Safe retention, archive, consolidation, and purge controls

-- ============================================================================
-- MIGRATION: Add retention columns to observations
-- ============================================================================

-- Add retention metadata to observations
ALTER TABLE observations
    ADD COLUMN IF NOT EXISTS retention_class VARCHAR(50) DEFAULT 'observation',
    ADD COLUMN IF NOT EXISTS retention_policy VARCHAR(100) DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS archive_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS delete_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS purge_protected BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS last_recalled_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS recall_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS duplicate_of UUID REFERENCES observations(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS consolidated_into UUID REFERENCES observations(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS has_canonical_representation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS has_summary_representation BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS storage_tier VARCHAR(20) DEFAULT 'hot' CHECK (storage_tier IN ('hot', 'cold', 'archived'));

-- Create retention class enum table
CREATE TABLE IF NOT EXISTS retention_classes (
    class_name VARCHAR(50) PRIMARY KEY,
    durability VARCHAR(20) NOT NULL DEFAULT 'semi' CHECK (durability IN ('durable', 'semi', 'temporary')),
    default_retention_days INTEGER,
    archive_after_days INTEGER,
    delete_after_days INTEGER,
    protect_by_default BOOLEAN DEFAULT FALSE,
    can_be_purged BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert retention classes
INSERT INTO retention_classes (class_name, durability, default_retention_days, archive_after_days, delete_after_days, protect_by_default, can_be_purged, description)
VALUES
    ('canonical', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'Canonical facts, never purge'),
    ('pinned', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'Pinned memories, never purge'),
    ('decision', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'Major decisions, never purge'),
    ('procedure', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'Procedures and how-tos, never purge'),
    ('preference', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'User preferences, never purge'),
    ('project_fact', 'durable', NULL, NULL, NULL, TRUE, FALSE, 'Project definitions, never purge'),
    ('summary', 'semi', NULL, 90, 365, FALSE, FALSE, 'Summaries, archive after 90d'),
    ('task_history', 'semi', 180, 90, 365, FALSE, TRUE, 'Task history, purge after 1y'),
    ('observation', 'semi', 90, 60, 180, FALSE, TRUE, 'Observations, archive after 60d'),
    ('checkpoint', 'temporary', 30, 14, 60, FALSE, TRUE, 'Checkpoints, cap per session'),
    ('raw_exchange', 'temporary', 60, 30, 90, FALSE, TRUE, 'Raw exchanges, archive after 30d'),
    ('ephemeral', 'temporary', 21, 7, 30, FALSE, TRUE, 'Ephemeral, purge after 30d'),
    ('superseded', 'temporary', 120, 60, 120, FALSE, TRUE, 'Superseded, grace period'),
    ('duplicate', 'temporary', 30, 14, 30, FALSE, TRUE, 'Duplicates, short grace')
ON CONFLICT (class_name) DO NOTHING;

-- ============================================================================
-- MIGRATION: Add retention metadata to raw_exchanges
-- ============================================================================

ALTER TABLE raw_exchanges
    ADD COLUMN IF NOT EXISTS retention_class VARCHAR(50) DEFAULT 'raw_exchange',
    ADD COLUMN IF NOT EXISTS archive_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS delete_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS purge_protected BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS storage_tier VARCHAR(20) DEFAULT 'hot' CHECK (storage_tier IN ('hot', 'cold', 'archived'));

-- ============================================================================
-- MIGRATION: Add retention metadata to summaries
-- ============================================================================

ALTER TABLE summaries
    ADD COLUMN IF NOT EXISTS retention_class VARCHAR(50) DEFAULT 'summary',
    ADD COLUMN IF NOT EXISTS archive_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS delete_eligible_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS purge_protected BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS storage_tier VARCHAR(20) DEFAULT 'hot' CHECK (storage_tier IN ('hot', 'cold', 'archived'));

-- ============================================================================
-- NEW TABLE: archive_storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS archive_storage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source reference
    original_table VARCHAR(100) NOT NULL,
    original_id UUID NOT NULL,
    
    -- Archived data (compressed JSONB)
    archived_data JSONB NOT NULL,
    
    -- Archive metadata
    archive_type VARCHAR(50) NOT NULL DEFAULT 'full', -- 'full', 'partial', 'reference'
    archive_reason VARCHAR(100), -- 'age', 'size', 'manual', 'consolidation'
    
    -- Retention tracking
    original_retention_class VARCHAR(50),
    original_created_at TIMESTAMP WITH TIME ZONE,
    original_importance_score DECIMAL(3,2),
    
    -- Archive timestamps
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archive_version INTEGER DEFAULT 1,
    
    -- Restoration support
    restorable BOOLEAN DEFAULT TRUE,
    restored_at TIMESTAMP WITH TIME ZONE,
    restored_to_id UUID,
    
    -- Storage tracking
    compressed_size_bytes INTEGER,
    original_size_bytes INTEGER,
    compression_ratio DECIMAL(3,2),
    
    -- Audit
    archived_by VARCHAR(100) DEFAULT 'system',
    archive_batch_id UUID
);

CREATE INDEX IF NOT EXISTS idx_archive_source ON archive_storage(original_table, original_id);
CREATE INDEX IF NOT EXISTS idx_archive_batch ON archive_storage(archive_batch_id);
CREATE INDEX IF NOT EXISTS idx_archive_restorable ON archive_storage(archived_at) WHERE restorable = TRUE;

-- ============================================================================
-- NEW TABLE: retention_actions
-- ============================================================================

CREATE TABLE IF NOT EXISTS retention_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Action metadata
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('consolidate', 'archive', 'purge', 'protect', 'unprotect')),
    action_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (action_status IN ('pending', 'running', 'completed', 'failed', 'dry_run')),
    
    -- Target records
    target_table VARCHAR(100) NOT NULL,
    target_count INTEGER,
    affected_ids UUID[],
    
    -- Action details
    records_consolidated INTEGER DEFAULT 0,
    records_archived INTEGER DEFAULT 0,
    records_purged INTEGER DEFAULT 0,
    records_protected INTEGER DEFAULT 0,
    
    -- Space tracking
    space_reclaimed_bytes BIGINT DEFAULT 0,
    space_archived_bytes BIGINT DEFAULT 0,
    
    -- Configuration used
    retention_policy_applied JSONB,
    
    -- Execution
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Audit
    triggered_by VARCHAR(100) DEFAULT 'system',
    dry_run BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_retention_actions_type ON retention_actions(action_type, action_status);
CREATE INDEX IF NOT EXISTS idx_retention_actions_created ON retention_actions(created_at DESC);

-- ============================================================================
-- NEW TABLE: retention_settings
-- ============================================================================

CREATE TABLE IF NOT EXISTS retention_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core protection settings
    keep_pinned_forever BOOLEAN DEFAULT TRUE,
    keep_canonical_forever BOOLEAN DEFAULT TRUE,
    keep_decisions_forever BOOLEAN DEFAULT TRUE,
    keep_procedures_forever BOOLEAN DEFAULT TRUE,
    keep_preferences_forever BOOLEAN DEFAULT TRUE,
    keep_project_facts_forever BOOLEAN DEFAULT TRUE,
    
    -- Retention periods (days)
    raw_exchanges_days INTEGER DEFAULT 60,
    ephemeral_days INTEGER DEFAULT 21,
    observation_days INTEGER DEFAULT 90,
    task_history_days INTEGER DEFAULT 180,
    superseded_grace_days INTEGER DEFAULT 120,
    duplicate_grace_days INTEGER DEFAULT 30,
    
    -- Limits
    checkpoints_max_per_session INTEGER DEFAULT 5,
    max_database_size_gb INTEGER DEFAULT 10,
    target_database_size_gb INTEGER DEFAULT 8,
    
    -- Archive behavior
    archive_before_delete BOOLEAN DEFAULT TRUE,
    archive_location VARCHAR(500) DEFAULT 'database', -- 'database', 'file', 's3'
    enable_cold_storage BOOLEAN DEFAULT TRUE,
    
    -- Job settings
    purge_batch_size INTEGER DEFAULT 1000,
    consolidate_before_purge BOOLEAN DEFAULT TRUE,
    enable_nightly_retention_job BOOLEAN DEFAULT TRUE,
    enable_dry_run BOOLEAN DEFAULT TRUE,
    
    -- Size control
    size_check_interval_hours INTEGER DEFAULT 24,
    
    -- Safety
    min_records_before_purge INTEGER DEFAULT 10000,
    
    -- Audit
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'system'
);

-- Insert default settings if empty
INSERT INTO retention_settings DEFAULT VALUES
ON CONFLICT DO NOTHING;

-- ============================================================================
-- INDEXES for retention queries
-- ============================================================================

-- Observations retention indexes
CREATE INDEX IF NOT EXISTS idx_obs_retention_class ON observations(retention_class);
CREATE INDEX IF NOT EXISTS idx_obs_archive_eligible ON observations(archive_eligible_at) WHERE archive_eligible_at IS NOT NULL AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_obs_delete_eligible ON observations(delete_eligible_at) WHERE delete_eligible_at IS NOT NULL AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_obs_storage_tier ON observations(storage_tier);
CREATE INDEX IF NOT EXISTS idx_obs_purge_protected ON observations(purge_protected) WHERE purge_protected = TRUE;
CREATE INDEX IF NOT EXISTS idx_obs_last_recalled ON observations(last_recalled_at);
CREATE INDEX IF NOT EXISTS idx_obs_recall_count ON observations(recall_count DESC);
CREATE INDEX IF NOT EXISTS idx_obs_duplicate ON observations(duplicate_of) WHERE duplicate_of IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_obs_consolidated ON observations(consolidated_into) WHERE consolidated_into IS NOT NULL;

-- Raw exchanges retention indexes
CREATE INDEX IF NOT EXISTS idx_raw_archive_eligible ON raw_exchanges(archive_eligible_at) WHERE archive_eligible_at IS NOT NULL AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_raw_delete_eligible ON raw_exchanges(delete_eligible_at) WHERE delete_eligible_at IS NOT NULL AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_raw_storage_tier ON raw_exchanges(storage_tier);

-- ============================================================================
-- VIEWS for retention monitoring
-- ============================================================================

-- Retention statistics view
CREATE OR REPLACE VIEW retention_stats AS
SELECT
    'observations' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE retention_class = 'canonical') as canonical_count,
    COUNT(*) FILTER (WHERE retention_class = 'pinned') as pinned_count,
    COUNT(*) FILTER (WHERE retention_class = 'decision') as decision_count,
    COUNT(*) FILTER (WHERE retention_class = 'summary') as summary_count,
    COUNT(*) FILTER (WHERE retention_class = 'observation') as observation_count,
    COUNT(*) FILTER (WHERE retention_class = 'raw_exchange') as raw_exchange_count,
    COUNT(*) FILTER (WHERE retention_class = 'ephemeral') as ephemeral_count,
    COUNT(*) FILTER (WHERE purge_protected = TRUE) as protected_count,
    COUNT(*) FILTER (WHERE archive_eligible_at IS NOT NULL AND archived_at IS NULL) as archive_candidates,
    COUNT(*) FILTER (WHERE delete_eligible_at IS NOT NULL AND archived_at IS NULL) as purge_candidates,
    COUNT(*) FILTER (WHERE storage_tier = 'archived') as archived_count,
    pg_size_pretty(pg_total_relation_size('observations')) as table_size
FROM observations

UNION ALL

SELECT
    'raw_exchanges' as table_name,
    COUNT(*) as total_records,
    0 as canonical_count,
    0 as pinned_count,
    0 as decision_count,
    0 as summary_count,
    0 as observation_count,
    COUNT(*) as raw_exchange_count,
    0 as ephemeral_count,
    COUNT(*) FILTER (WHERE purge_protected = TRUE) as protected_count,
    COUNT(*) FILTER (WHERE archive_eligible_at IS NOT NULL AND archived_at IS NULL) as archive_candidates,
    COUNT(*) FILTER (WHERE delete_eligible_at IS NOT NULL AND archived_at IS NULL) as purge_candidates,
    COUNT(*) FILTER (WHERE storage_tier = 'archived') as archived_count,
    pg_size_pretty(pg_total_relation_size('raw_exchanges')) as table_size
FROM raw_exchanges;

-- Archive candidates view
CREATE OR REPLACE VIEW archive_candidates AS
SELECT 
    id,
    retention_class,
    content,
    importance_score,
    recall_count,
    archive_eligible_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/86400 as age_days
FROM observations
WHERE archive_eligible_at IS NOT NULL 
    AND archived_at IS NULL
    AND purge_protected = FALSE
    AND storage_tier = 'hot'
ORDER BY archive_eligible_at ASC;

-- Purge candidates view (with safety filters)
CREATE OR REPLACE VIEW purge_candidates AS
SELECT 
    o.id,
    o.retention_class,
    rc.durability,
    o.content,
    o.importance_score,
    o.recall_count,
    o.last_recalled_at,
    o.delete_eligible_at,
    EXTRACT(EPOCH FROM (NOW() - o.created_at))/86400 as age_days,
    o.has_canonical_representation,
    o.has_summary_representation
FROM observations o
JOIN retention_classes rc ON rc.class_name = o.retention_class
WHERE o.delete_eligible_at IS NOT NULL 
    AND o.archived_at IS NULL
    AND o.purge_protected = FALSE
    AND o.storage_tier = 'hot'
    AND o.pinned = FALSE
    AND o.canonical = FALSE
    AND rc.can_be_purged = TRUE
    -- Safety: must have representation if important
    AND (
        o.importance_score < 0.7
        OR (o.has_canonical_representation = TRUE OR o.has_summary_representation = TRUE)
    )
ORDER BY o.delete_eligible_at ASC;

-- Protected records view
CREATE OR REPLACE VIEW protected_records AS
SELECT 
    id,
    retention_class,
    content,
    importance_score,
    pinned,
    canonical,
    purge_protected,
    recall_count,
    CASE 
        WHEN pinned THEN 'pinned'
        WHEN canonical THEN 'canonical'
        WHEN retention_class IN ('decision', 'procedure', 'preference', 'project_fact') THEN 'durable_class'
        WHEN importance_score > 0.9 THEN 'high_importance'
        WHEN recall_count > 10 THEN 'frequently_recalled'
        ELSE 'unknown'
    END as protection_reason
FROM observations
WHERE purge_protected = TRUE
    OR pinned = TRUE
    OR canonical = TRUE
    OR retention_class IN ('canonical', 'pinned', 'decision', 'procedure', 'preference', 'project_fact');

-- ============================================================================
-- FUNCTIONS for retention operations
-- ============================================================================

-- Function to classify retention
CREATE OR REPLACE FUNCTION classify_retention(
    p_content TEXT,
    p_tags TEXT[],
    p_importance DECIMAL
) RETURNS VARCHAR(50) AS $$
DECLARE
    v_class VARCHAR(50) := 'observation';
BEGIN
    -- Check for durable classes based on tags/content
    IF p_tags && ARRAY['canonical', 'decision', 'procedure'] THEN
        IF 'canonical' = ANY(p_tags) THEN v_class := 'canonical'; END IF;
        IF 'decision' = ANY(p_tags) THEN v_class := 'decision'; END IF;
        IF 'procedure' = ANY(p_tags) THEN v_class := 'procedure'; END IF;
    END IF;
    
    -- High importance observations
    IF p_importance >= 0.9 THEN
        v_class := 'summary';
    END IF;
    
    -- Check for ephemeral
    IF p_tags && ARRAY['ephemeral', 'temp', 'draft'] THEN
        v_class := 'ephemeral';
    END IF;
    
    RETURN v_class;
END;
$$ LANGUAGE plpgsql;

-- Function to compute archive eligibility
CREATE OR REPLACE FUNCTION compute_archive_eligibility(
    p_retention_class VARCHAR(50),
    p_created_at TIMESTAMP WITH TIME ZONE,
    p_last_recalled_at TIMESTAMP WITH TIME ZONE,
    p_recall_count INTEGER
) RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    v_archive_after INTEGER;
    v_eligible_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get archive period for class
    SELECT archive_after_days INTO v_archive_after
    FROM retention_classes
    WHERE class_name = p_retention_class;
    
    IF v_archive_after IS NULL THEN
        RETURN NULL; -- Never archive
    END IF;
    
    -- Compute eligibility (after days from creation OR last recall)
    v_eligible_at := GREATEST(
        p_created_at + (v_archive_after || ' days')::INTERVAL,
        COALESCE(p_last_recalled_at, p_created_at) + (v_archive_after / 2 || ' days')::INTERVAL
    );
    
    RETURN v_eligible_at;
END;
$$ LANGUAGE plpgsql;

-- Function to compute delete eligibility
CREATE OR REPLACE FUNCTION compute_delete_eligibility(
    p_retention_class VARCHAR(50),
    p_created_at TIMESTAMP WITH TIME ZONE,
    p_archived_at TIMESTAMP WITH TIME ZONE
) RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    v_delete_after INTEGER;
    v_eligible_at TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Get delete period for class
    SELECT delete_after_days INTO v_delete_after
    FROM retention_classes
    WHERE class_name = p_retention_class;
    
    IF v_delete_after IS NULL THEN
        RETURN NULL; -- Never delete
    END IF;
    
    -- Compute from archive date if archived, else creation
    IF p_archived_at IS NOT NULL THEN
        v_eligible_at := p_archived_at + ((v_delete_after - COALESCE(
            (SELECT archive_after_days FROM retention_classes WHERE class_name = p_retention_class), 0
        )) || ' days')::INTERVAL;
    ELSE
        v_eligible_at := p_created_at + (v_delete_after || ' days')::INTERVAL;
    END IF;
    
    RETURN v_eligible_at;
END;
$$ LANGUAGE plpgsql;

-- Function to update archive eligibility for all records
CREATE OR REPLACE FUNCTION update_archive_eligibility() RETURNS INTEGER AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    UPDATE observations
    SET archive_eligible_at = compute_archive_eligibility(
        retention_class,
        created_at,
        last_recalled_at,
        recall_count
    )
    WHERE archive_eligible_at IS NULL
        AND retention_class IN (SELECT class_name FROM retention_classes WHERE archive_after_days IS NOT NULL);
    
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated;
END;
$$ LANGUAGE plpgsql;

-- Function to update delete eligibility for all records
CREATE OR REPLACE FUNCTION update_delete_eligibility() RETURNS INTEGER AS $$
DECLARE
    v_updated INTEGER := 0;
BEGIN
    UPDATE observations
    SET delete_eligible_at = compute_delete_eligibility(
        retention_class,
        created_at,
        archived_at
    )
    WHERE delete_eligible_at IS NULL
        AND retention_class IN (SELECT class_name FROM retention_classes WHERE delete_after_days IS NOT NULL);
    
    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated;
END;
$$ LANGUAGE plpgsql;

-- Function to protect a memory record
CREATE OR REPLACE FUNCTION protect_memory(p_record_id UUID) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE observations
    SET purge_protected = TRUE,
        updated_at = NOW()
    WHERE id = p_record_id;
    
    IF FOUND THEN
        RAISE NOTICE 'Memory % is now protected from purge', p_record_id;
        RETURN TRUE;
    ELSE
        RAISE NOTICE 'Memory % not found', p_record_id;
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to unprotect a memory record
CREATE OR REPLACE FUNCTION unprotect_memory(p_record_id UUID) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE observations
    SET purge_protected = FALSE,
        updated_at = NOW()
    WHERE id = p_record_id;
    
    IF FOUND THEN
        RAISE NOTICE 'Memory % is no longer protected', p_record_id;
        RETURN TRUE;
    ELSE
        RAISE NOTICE 'Memory % not found', p_record_id;
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERSION UPDATE
-- ============================================================================

COMMENT ON DATABASE CURRENT_DATABASE IS 'pg-memory v3.2.0 — Retention, Archive, Consolidation, and Safe Purge Controls';

-- Update settings
UPDATE pg_memory_settings 
SET setting_value = '3.2.0'
WHERE setting_key = 'schema_version';

-- Run eligibility updates
SELECT update_archive_eligibility();
SELECT update_delete_eligibility();

SELECT 'pg-memory v3.2.0 retention schema installed successfully' as status;
