"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWorkspace } from "@/components/WorkspaceContext";

export default function CompareRedirect() {
  const router = useRouter();
  const { activeWorkspaceId, isLoading } = useWorkspace();

  useEffect(() => {
    if (!isLoading) {
      if (activeWorkspaceId) {
        router.replace(`/workspaces/${activeWorkspaceId}/compare`);
      } else {
        router.replace("/workspaces");
      }
    }
  }, [activeWorkspaceId, isLoading, router]);

  return <div className="flex h-screen items-center justify-center text-muted-foreground text-sm">Redirecting to workspace...</div>;
}
