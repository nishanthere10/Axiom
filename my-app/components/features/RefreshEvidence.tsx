"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { submitResearch, getJobStatus } from "@/lib/api";

const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 30; // 60 seconds max

export default function RefreshEvidence({ question, onRefresh }: { question: string; onRefresh: (sessionId: string) => void }) {
  const { getToken } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      setError(null);

      const token = await getToken() ?? "";
      // Start a new research run with force_refresh=true
      const res = await submitResearch(question, true, token);
      const { session_id, job_id } = res;

      // Poll until job is done or failed
      let polls = 0;
      while (polls < MAX_POLLS) {
        await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
        const job = await getJobStatus(job_id, token);

        if (job.status === "completed") {
          onRefresh(session_id);
          return;
        }
        if (job.status === "failed") {
          setError("Evidence refresh failed. Please try again.");
          return;
        }
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
    <div className="flex flex-col items-end mb-6 gap-1">
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className="flex items-center space-x-2 text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
      >
        <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
        <span>{isRefreshing ? "Fetching fresh evidence…" : "Refresh Evidence"}</span>
      </button>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
