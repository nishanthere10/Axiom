"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { ChevronLeft, FlaskConical, BookMarked, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

import { useToast } from "@/components/ui/ToastProvider";

const DECISION_STATUS_COLORS: Record<string, string> = {
  PROPOSED:    "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  APPROVED:    "bg-green-500/10  text-green-500  border-green-500/20",
  IMPLEMENTED: "bg-blue-500/10   text-blue-500   border-blue-500/20",
  REJECTED:    "bg-red-500/10    text-red-500    border-red-500/20",
  ARCHIVED:    "bg-gray-500/10   text-gray-400   border-gray-500/20",
};

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const { toast } = useToast();
  const workspaceId = params.id as string;
  const projectId = params.project_id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken();
        if (!token) return;
        const result = await apiFetch<any>(
          `/workspaces/${workspaceId}/projects/${projectId}`,
          token, { getToken }
        );
        setData(result);
      } catch (e: any) {
        console.error("Failed to load project", e);
        const msg = e?.message || "Failed to load project details.";
        setErrorMsg(msg);
        toast(msg, "error");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId, projectId, getToken]);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );

  if (errorMsg || !data) return (
    <div className="p-6 space-y-4">
      <button
        onClick={() => router.push(`/workspaces/${workspaceId}/projects`)}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="w-4 h-4" /> Back to Projects
      </button>
      <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
        {errorMsg || "Project not found."}
      </div>
    </div>
  );

  const { project, research, decisions } = data;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 animate-in fade-in duration-300">
      {/* Back */}
      <button
        onClick={() => router.push(`/workspaces/${workspaceId}/projects`)}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="w-4 h-4" /> All Projects
      </button>

      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">{project.name}</h1>
        {project.description && (
          <p className="text-sm text-muted-foreground">{project.description}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })} · {project.status}
        </p>
      </div>

      {/* Research Sessions */}
      <section className="border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-border/50 bg-surface/50 flex items-center justify-between">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-muted-foreground" />
            Research Sessions
            <span className="text-xs text-muted-foreground font-normal">({research.length})</span>
          </h2>
          <button
            onClick={() => router.push(`/workspaces/${workspaceId}/research?project_id=${projectId}`)}
            className="flex items-center gap-1.5 text-xs text-primary hover:underline"
          >
            <Plus className="w-3.5 h-3.5" /> New Research
          </button>
        </div>
        <div className="divide-y divide-border/50">
          {research.length === 0 ? (
            <div className="p-6 text-center">
              <p className="text-sm text-muted-foreground">No research sessions in this project yet.</p>
            </div>
          ) : (
            research.map((session: any) => (
              <div
                key={session.id}
                onClick={() => router.push(`/workspaces/${workspaceId}/research?session_id=${session.id}`)}
                className="px-5 py-3 hover:bg-surface/50 cursor-pointer transition-colors"
              >
                <p className="text-sm text-foreground line-clamp-1">{session.question}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {formatDistanceToNow(new Date(session.created_at), { addSuffix: true })}
                </p>
              </div>
            ))
          )}
        </div>
      </section>

      {/* Decisions */}
      <section className="border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-border/50 bg-surface/50 flex items-center justify-between">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <BookMarked className="w-4 h-4 text-muted-foreground" />
            Decisions
            <span className="text-xs text-muted-foreground font-normal">({decisions.length})</span>
          </h2>
          <button
            onClick={() => router.push(`/workspaces/${workspaceId}/decisions`)}
            className="text-xs text-primary hover:underline"
          >
            View all
          </button>
        </div>
        <div className="divide-y divide-border/50">
          {decisions.length === 0 ? (
            <div className="p-6 text-center">
              <p className="text-sm text-muted-foreground">No decisions in this project yet.</p>
            </div>
          ) : (
            decisions.map((decision: any) => (
              <div
                key={decision.id}
                onClick={() => router.push(`/workspaces/${workspaceId}/decisions/${decision.id}`)}
                className="px-5 py-3 hover:bg-surface/50 cursor-pointer transition-colors flex items-center justify-between gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground line-clamp-1">{decision.title}</p>
                  {decision.question && (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{decision.question}</p>
                  )}
                </div>
                <span className={cn("shrink-0 text-xs px-2 py-0.5 rounded-full border", DECISION_STATUS_COLORS[decision.status] || DECISION_STATUS_COLORS.PROPOSED)}>
                  {decision.status.charAt(0) + decision.status.slice(1).toLowerCase()}
                </span>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
