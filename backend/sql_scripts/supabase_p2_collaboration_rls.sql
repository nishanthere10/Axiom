-- Phase 1 Collaboration: RLS Policy Updates
-- Run this in the Supabase Dashboard SQL Editor

-- 1. research_sessions
DROP POLICY IF EXISTS "Users can manage their own sessions" ON public.research_sessions;
CREATE POLICY "Workspace members can manage research sessions"
    ON public.research_sessions FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members
            WHERE workspace_members.workspace_id = research_sessions.workspace_id
            AND workspace_members.user_id = auth.uid()::text
        )
    );

-- 2. decision_records
DROP POLICY IF EXISTS "Users can manage decision records in their workspaces" ON public.decision_records;
CREATE POLICY "Workspace members can manage decision records"
    ON public.decision_records FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members
            WHERE workspace_members.workspace_id = decision_records.workspace_id
            AND workspace_members.user_id = auth.uid()::text
        )
    );

-- 2b. research_reports (formerly decision_documents)
DROP POLICY IF EXISTS "Users can manage research reports in their workspaces" ON public.research_reports;
CREATE POLICY "Workspace members can manage research reports"
    ON public.research_reports FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members
            WHERE workspace_members.workspace_id = research_reports.workspace_id
            AND workspace_members.user_id = auth.uid()::text
        )
    );

-- 3. memory_items
-- Assuming existing policy is 'Users can manage their own memories'
DROP POLICY IF EXISTS "Users can manage their own memories" ON public.memory_items;
CREATE POLICY "Workspace members can manage memory items"
    ON public.memory_items FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members
            WHERE workspace_members.workspace_id = memory_items.workspace_id
            AND workspace_members.user_id = auth.uid()::text
        )
    );

-- 4. github_repositories
DROP POLICY IF EXISTS "Users can manage their own github repositories" ON public.github_repositories;
CREATE POLICY "Workspace members can manage github repositories"
    ON public.github_repositories FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members
            WHERE workspace_members.workspace_id = github_repositories.workspace_id
            AND workspace_members.user_id = auth.uid()::text
        )
    );
