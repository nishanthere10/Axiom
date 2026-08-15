CREATE TABLE IF NOT EXISTS public.workspace_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(workspace_id, user_id)
);

-- Backfill data from workspaces table
INSERT INTO public.workspace_members (workspace_id, user_id, role)
SELECT id, user_id, 'owner'
FROM public.workspaces
ON CONFLICT (workspace_id, user_id) DO NOTHING;

ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own workspace memberships"
    ON public.workspace_members FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Workspace owners can manage members"
    ON public.workspace_members FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.workspace_members owner
            WHERE owner.workspace_id = workspace_members.workspace_id
            AND owner.user_id = auth.uid()::text
            AND owner.role = 'owner'
        )
    );
