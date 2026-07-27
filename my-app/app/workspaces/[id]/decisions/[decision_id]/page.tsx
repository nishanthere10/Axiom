"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { formatDistanceToNow, format } from "date-fns";
import { ChevronLeft, Clock, GitBranch, FileText, CheckCircle2, XCircle, Archive } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/ToastProvider";

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  PROPOSED:    { label: "Proposed",    color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",    icon: <Clock className="w-3.5 h-3.5" /> },
  APPROVED:    { label: "Approved",    color: "bg-green-500/10 text-green-500 border-green-500/20",       icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
  IMPLEMENTED: { label: "Implemented", color: "bg-blue-500/10 text-blue-500 border-blue-500/20",          icon: <CheckCircle2 className="w-3.5 h-3.5" /> },
  REJECTED:    { label: "Rejected",    color: "bg-red-500/10 text-red-500 border-red-500/20",             icon: <XCircle className="w-3.5 h-3.5" /> },
  SUPERSEDED:  { label: "Superseded",  color: "bg-purple-500/10 text-purple-400 border-purple-500/20",    icon: <Archive className="w-3.5 h-3.5" /> },
  ARCHIVED:    { label: "Archived",    color: "bg-gray-500/10 text-gray-400 border-gray-500/20",          icon: <Archive className="w-3.5 h-3.5" /> },
};

const STATUS_FLOW = ["PROPOSED", "APPROVED", "IMPLEMENTED"];

export default function DecisionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const workspaceId = params.id as string;
  const decisionId = params.decision_id as string;
  const { toast } = useToast();

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [pendingStatus, setPendingStatus] = useState("");
  const [note, setNote] = useState("");
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken();
        if (!token) return;
        const result = await apiFetch<any>(
          `/workspaces/${workspaceId}/decisions/${decisionId}/full`,
          token, { getToken }
        );
        setData(result);
      } catch (e) {
        console.error("Failed to load decision", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId, decisionId, getToken]);

  const initiateStatusChange = (newStatus: string) => {
    setPendingStatus(newStatus);
    setNote("");
    setShowNoteModal(true);
  };

  const confirmStatusChange = async () => {
    setUpdating(true);
    try {
      const token = await getToken();
      if (!token) return;
      const updated = await apiFetch<any>(
        `/workspaces/${workspaceId}/decisions/${decisionId}`,
        token,
        {
          method: "PATCH",
          body: JSON.stringify({ status: pendingStatus, note: note || undefined }),
          getToken,
        }
      );
      // Reload full data to get updated history
      const fresh = await apiFetch<any>(
        `/workspaces/${workspaceId}/decisions/${decisionId}/full`,
        token, { getToken }
      );
      setData(fresh);
      setShowNoteModal(false);
      toast("Decision status updated", "success");
    } catch (e: any) {
      console.error("Failed to update status", e);
      toast(e?.message || "Failed to update status", "error");
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!data) return <div className="p-6 text-muted-foreground">Decision not found.</div>;

  const { decision, research, history } = data;
  const currentStatus = decision.status;
  const statusCfg = STATUS_CONFIG[currentStatus] || STATUS_CONFIG.PROPOSED;
  const nextStatuses = STATUS_FLOW.filter(s => s !== currentStatus);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Back button */}
      <button
        onClick={() => router.push(`/workspaces/${workspaceId}/decisions`)}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ChevronLeft className="w-4 h-4" /> All Decisions
      </button>

      {/* Header */}
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-semibold text-foreground">{decision.title}</h1>
          <span className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium shrink-0", statusCfg.color)}>
            {statusCfg.icon}
            {statusCfg.label}
          </span>
        </div>
        <p className="text-xs text-muted-foreground font-mono">
          Created {format(new Date(decision.created_at), "MMM d, yyyy")} · ID {decision.id.substring(0, 8)}
        </p>
      </div>

      {/* Status change actions */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Move to:</span>
        {nextStatuses.map(s => (
          <button
            key={s}
            onClick={() => initiateStatusChange(s)}
            className={cn("px-3 py-1 rounded-full text-xs border font-medium hover:opacity-80 transition-opacity", STATUS_CONFIG[s]?.color)}
          >
            {STATUS_CONFIG[s]?.label}
          </button>
        ))}
        {currentStatus !== "REJECTED" && (
          <button
            onClick={() => initiateStatusChange("REJECTED")}
            className="px-3 py-1 rounded-full text-xs border border-red-500/20 text-red-500 bg-red-500/10 font-medium hover:opacity-80 transition-opacity"
          >
            Reject
          </button>
        )}
        {currentStatus !== "SUPERSEDED" && (
          <button
            onClick={() => initiateStatusChange("SUPERSEDED")}
            className="px-3 py-1 rounded-full text-xs border border-purple-500/20 text-purple-400 bg-purple-500/10 font-medium hover:opacity-80 transition-opacity"
          >
            Supersede
          </button>
        )}
        {currentStatus !== "ARCHIVED" && (
          <button
            onClick={() => initiateStatusChange("ARCHIVED")}
            className="px-3 py-1 rounded-full text-xs border border-gray-500/20 text-gray-400 bg-gray-500/10 font-medium hover:opacity-80 transition-opacity"
          >
            Archive
          </button>
        )}
      </div>

      {/* Research context */}
      <section className="border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-border/50 bg-surface/50">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <FileText className="w-4 h-4 text-muted-foreground" /> Research Context
          </h2>
        </div>
        <div className="p-5 space-y-4">
          {research.question && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Question</p>
              <p className="text-sm text-foreground">{research.question}</p>
            </div>
          )}
          {research.executive_summary && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Executive Summary</p>
              <p className="text-sm text-foreground/80 leading-relaxed">{research.executive_summary}</p>
            </div>
          )}
          {research.recommendation_context && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Recommendation</p>
              <p className="text-sm text-foreground/80 leading-relaxed">{research.recommendation_context}</p>
            </div>
          )}
          {research.confidence && Object.keys(research.confidence).length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Confidence Scores</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(research.confidence).map(([key, val]) => (
                  <div key={key} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="text-foreground font-mono">{Math.round(Number(val) * 100)}%</span>
                    </div>
                    <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                      <div className="h-full bg-primary rounded-full" style={{ width: `${Math.round(Number(val) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {research.alternatives && (
            <details className="group">
              <summary className="text-xs font-medium text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors">
                Alternatives Considered ▸
              </summary>
              <p className="text-sm text-foreground/70 leading-relaxed mt-2 pl-2 border-l border-border">
                {research.alternatives}
              </p>
            </details>
          )}
        </div>
      </section>

      {/* Status history */}
      <section className="border border-border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-border/50 bg-surface/50">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Clock className="w-4 h-4 text-muted-foreground" /> Status History
          </h2>
        </div>
        <div className="p-5">
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">No history yet.</p>
          ) : (
            <div className="relative">
              <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />
              <div className="space-y-4">
                {history.map((h: any, i: number) => (
                  <div key={h.id} className="flex gap-3 relative">
                    <div className={cn("w-3.5 h-3.5 rounded-full border-2 shrink-0 mt-0.5 z-10",
                      i === history.length - 1 ? "bg-primary border-primary" : "bg-background border-border"
                    )} />
                    <div className="flex-1 min-w-0 pb-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {h.from_status && (
                          <>
                            <span className={cn("text-xs px-2 py-0.5 rounded-full border", STATUS_CONFIG[h.from_status]?.color)}>
                              {STATUS_CONFIG[h.from_status]?.label || h.from_status}
                            </span>
                            <span className="text-muted-foreground text-xs">→</span>
                          </>
                        )}
                        <span className={cn("text-xs px-2 py-0.5 rounded-full border", STATUS_CONFIG[h.to_status]?.color)}>
                          {STATUS_CONFIG[h.to_status]?.label || h.to_status}
                        </span>
                      </div>
                      {h.note && (
                        <p className="text-xs text-muted-foreground mt-1 italic">"{h.note}"</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {formatDistanceToNow(new Date(h.changed_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Actions bar */}
      <div className="flex items-center gap-3 pt-2 border-t border-border/50">
        <button
          onClick={() => router.push(`/workspaces/${workspaceId}/research?session_id=${decision.research_session_id}`)}
          className="text-xs text-primary underline underline-offset-4 hover:no-underline transition-all"
        >
          View original research
        </button>
      </div>

      {/* Note modal */}
      {showNoteModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background border border-border rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-semibold">
              Move to <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-sm",
                STATUS_CONFIG[pendingStatus]?.color)}>{STATUS_CONFIG[pendingStatus]?.label}</span>
            </h3>
            <div>
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Reason (optional)
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Why is this being moved?"
                className="mt-1.5 w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                rows={3}
              />
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowNoteModal(false)}
                className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                Cancel
              </button>
              <button
                onClick={confirmStatusChange}
                disabled={updating}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {updating ? "Saving…" : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
