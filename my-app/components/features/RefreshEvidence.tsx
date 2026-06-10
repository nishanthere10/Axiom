"use client";

import { useState } from "react";
import { RefreshCw, Loader2 } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { submitResearch, getJobStatus } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 30; // 60 seconds max

export default function RefreshEvidence({
  question,
  onRefresh,
}: {
  question: string;
  onRefresh: (sessionId: string) => void;
}) {
  const { getToken } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      setError(null);

      const token = (await getToken()) ?? "";
      const res = await submitResearch(question, true, token);
      const { session_id, job_id } = res;

      let polls = 0;
      while (polls < MAX_POLLS) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
        const job = await getJobStatus(job_id, token);
        if (job.status === "completed") { onRefresh(session_id); return; }
        if (job.status === "failed")    { setError("Evidence refresh failed. Please try again."); return; }
        polls++;
      }
      setError("Refresh timed out. Please try again.");
    } catch (err) {
      console.error("Failed to refresh evidence:", err);
      setError("An unexpected error occurred.");
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1.5">
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground border border-border hover:border-border/80 bg-surface hover:bg-surface-hover px-3 py-1.5 rounded-md transition-all duration-200 disabled:opacity-50 font-mono"
      >
        {isRefreshing
          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
          : <RefreshCw className="w-3.5 h-3.5" />}
        {isRefreshing ? "Refreshing evidence…" : "Refresh Evidence"}
      </button>
      {error && (
        <p className="text-xs text-destructive-foreground bg-destructive/10 border border-destructive/30 px-2 py-1 rounded-md">
          {error}
        </p>
      )}
    </div>
  );
}
