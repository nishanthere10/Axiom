-- 🔐 FIX 3.1: N+1 Query Optimization
-- Consolidate dashboard queries into single RPC function
-- Reduces 6+ round-trips to 1

CREATE OR REPLACE FUNCTION get_workspace_dashboard_data(p_workspace_id UUID, p_user_id UUID)
RETURNS JSON AS $$
DECLARE
    v_workspace JSON;
    v_decision_summary JSON;
    v_research_summary JSON;
    v_memory_summary JSON;
    v_comparison_summary JSON;
    v_repo_summary JSON;
    v_recent_decisions JSON;
    v_recent_research JSON;
    v_recent_comparisons JSON;
    v_connected_repos JSON;
    v_quick_insights JSON;
BEGIN
    -- Verify workspace access
    IF NOT EXISTS (
        SELECT 1 FROM workspace_members 
        WHERE workspace_id = p_workspace_id AND user_id = p_user_id
    ) THEN
        RETURN NULL;
    END IF;
    
    -- Get workspace
    SELECT row_to_json(w) INTO v_workspace
    FROM workspaces w
    WHERE w.id = p_workspace_id AND w.deleted_at IS NULL;
    
    IF v_workspace IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Decision summary (counts by status)
    SELECT json_build_object(
        'proposed', COALESCE(SUM(CASE WHEN status = 'proposed' THEN 1 ELSE 0 END), 0),
        'approved', COALESCE(SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END), 0),
        'implemented', COALESCE(SUM(CASE WHEN status = 'implemented' THEN 1 ELSE 0 END), 0),
        'rejected', COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0),
        'archived', COALESCE(SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END), 0)
    ) INTO v_decision_summary
    FROM decision_records
    WHERE workspace_id = p_workspace_id;
    
    -- Research summary
    SELECT json_build_object(
        'total_sessions', COUNT(*),
        'active_sessions', SUM(CASE WHEN status IN ('active', 'processing') THEN 1 ELSE 0 END)
    ) INTO v_research_summary
    FROM research_sessions
    WHERE workspace_id = p_workspace_id;
    
    -- Memory summary
    SELECT json_build_object(
        'global_memories', (SELECT COUNT(*) FROM memory_items WHERE scope = 'global'),
        'workspace_memories', (SELECT COUNT(*) FROM memory_items WHERE scope = 'workspace:' || p_workspace_id::text),
        'pinned_memories', (SELECT COUNT(*) FROM memory_items WHERE workspace_id = p_workspace_id AND is_pinned = true)
    ) INTO v_memory_summary;
    
    -- Comparison summary
    SELECT json_build_object('total_comparisons', COUNT(*)) INTO v_comparison_summary
    FROM comparisons
    WHERE workspace_id = p_workspace_id;
    
    -- Repo summary
    SELECT json_build_object('connected_repos', COUNT(*)) INTO v_repo_summary
    FROM github_repositories
    WHERE workspace_id = p_workspace_id AND is_active = true;
    
    -- Recent decisions (last 5)
    SELECT COALESCE(json_agg(row_to_json(d) ORDER BY d.created_at DESC), '[]'::json) INTO v_recent_decisions
    FROM (
        SELECT * FROM decision_records
        WHERE workspace_id = p_workspace_id
        ORDER BY created_at DESC
        LIMIT 5
    ) d;
    
    -- Recent research (last 5)
    SELECT COALESCE(json_agg(row_to_json(r) ORDER BY r.created_at DESC), '[]'::json) INTO v_recent_research
    FROM (
        SELECT * FROM research_sessions
        WHERE workspace_id = p_workspace_id
        ORDER BY created_at DESC
        LIMIT 5
    ) r;
    
    -- Recent comparisons (last 5)
    SELECT COALESCE(json_agg(row_to_json(c) ORDER BY c.created_at DESC), '[]'::json) INTO v_recent_comparisons
    FROM (
        SELECT * FROM comparisons
        WHERE workspace_id = p_workspace_id
        ORDER BY created_at DESC
        LIMIT 5
    ) c;
    
    -- Connected repos with profiles (last 5)
    SELECT COALESCE(json_agg(
        json_build_object(
            'id', gr.id,
            'repository_name', gr.repository_name,
            'repository_owner', gr.repository_owner,
            'last_sync_at', gr.last_sync_at,
            'indexed_file_count', gr.indexed_file_count,
            'total_file_count', gr.total_file_count,
            'profile', (
                SELECT row_to_json(grp)
                FROM github_repository_profiles grp
                WHERE grp.github_repository_id = gr.id
                LIMIT 1
            )
        ) ORDER BY gr.created_at DESC
    ), '[]'::json) INTO v_connected_repos
    FROM (
        SELECT * FROM github_repositories
        WHERE workspace_id = p_workspace_id AND is_active = true
        ORDER BY created_at DESC
        LIMIT 5
    ) gr;
    
    -- Quick insights (most common decision category, most referenced repo)
    SELECT json_build_object(
        'most_common_decision_category', (
            SELECT category
            FROM decision_records
            WHERE workspace_id = p_workspace_id AND category IS NOT NULL
            GROUP BY category
            ORDER BY COUNT(*) DESC
            LIMIT 1
        ),
        'most_referenced_repository', (
            SELECT repository_name
            FROM github_repositories
            WHERE workspace_id = p_workspace_id AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
        ),
        'most_active_research_area', NULL
    ) INTO v_quick_insights;
    
    -- Build final response
    RETURN json_build_object(
        'workspace', v_workspace,
        'decision_summary', v_decision_summary,
        'research_summary', v_research_summary,
        'memory_summary', v_memory_summary,
        'comparison_summary', v_comparison_summary,
        'repository_summary', v_repo_summary,
        'recent_decisions', v_recent_decisions,
        'recent_research', v_recent_research,
        'recent_comparisons', v_recent_comparisons,
        'connected_repositories', v_connected_repos,
        'quick_insights', v_quick_insights
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
