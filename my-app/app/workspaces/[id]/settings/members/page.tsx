"use client";

import { MembersList } from "@/components/features/MembersList";
import { useWorkspace } from "@/components/WorkspaceContext";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function MembersPage() {
  const { activeWorkspaceId } = useWorkspace();

  if (!activeWorkspaceId) return null;

  return (
    <div className="relative w-full min-h-[calc(100vh-8rem)] flex flex-col pt-12 md:pt-20 max-w-4xl mx-auto px-6 space-y-8">
      <div className="mb-6 flex items-center">
        <Link href={`/workspaces/${activeWorkspaceId}/settings`} className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mr-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Settings
        </Link>
      </div>

      <div className="mb-10">
        <h1 className="text-3xl font-medium tracking-tight text-foreground">Workspace Members</h1>
        <p className="text-sm text-muted-foreground mt-2">Manage who has access to this workspace and their roles.</p>
      </div>

      <MembersList workspaceId={activeWorkspaceId} />
    </div>
  );
}
