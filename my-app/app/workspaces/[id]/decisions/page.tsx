"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { BookMarked, Clock, CheckCircle2, XCircle, Archive, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  PROPOSED:    { label: "Proposed",    color: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
  APPROVED:    { label: "Approved",    color: "bg-green-500/10 text-green-500 border-green-500/20" },
  IMPLEMENTED: { label: "Implemented", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  REJECTED:    { label: "Rejected",    color: "bg-red-500/10 text-red-500 border-red-500/20" },
  SUPERSEDED:  { label: "Superseded",  color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  ARCHIVED:    { label: "Archived",    color: "bg-gray-500/10 text-gray-400 border-gray-500/20" },
};

export default function DecisionsPage() {
  const params = useParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const workspaceId = params.id as string;

  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    async function fetchDecisions() {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await apiFetch<{ decisions: any[] }>(
          `/workspaces/${workspaceId}/decisions`,
          token, { getToken }
        );
        setDecisions(data.decisions || []);
      } catch (e) {
        console.error("Failed to fetch decisions", e);
      } finally {
        setLoading(false);
      }
    }
    fetchDecisions();
  }, [workspaceId, getToken]);

  const handleSearch = async () => {
    if (!searchQuery && !statusFilter) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const token = await getToken();
      if (!token) return;
      const params = new URLSearchParams();
      if (searchQuery) params.set("q", searchQuery);
      if (statusFilter) params.set("status", statusFilter);
      const data = await apiFetch<{ results: any[] }>(
        `/workspaces/${workspaceId}/decisions/search?${params}`,
        token, { getToken }
      );
      setSearchResults(data.results || []);
    } catch (e) {
      console.error("Search failed", e);
    } finally {
      setSearching(false);
    }
  };

  const displayed = searchResults ?? decisions;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Decisions</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Architecture decisions and their history.
          </p>
        </div>
        <button
          onClick={() => router.push(`/workspaces/${workspaceId}/research`)}
          className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors shrink-0"
        >
          + New Research
        </button>
      </div>

      {/* Search bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search decisions…"
            className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All statuses</option>
          {Object.keys(STATUS_CONFIG).map(s => (
            <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
          ))}
        </select>
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-4 py-2 bg-primary/10 border border-primary/20 text-primary rounded-lg text-sm hover:bg-primary/20 transition-colors disabled:opacity-50"
        >
          {searching ? "…" : "Search"}
        </button>
        {searchResults !== null && (
          <button
            onClick={() => { setSearchResults(null); setSearchQuery(""); setStatusFilter(""); }}
            className="px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Timeline */}
      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : displayed.length === 0 ? (
        <div className="text-center py-20 border border-dashed border-border/50 rounded-xl">
          <BookMarked className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
          <h3 className="text-base font-medium text-foreground">
            {searchResults !== null ? "No decisions match your search" : "No decisions yet"}
          </h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-xs mx-auto">
            {searchResults !== null
              ? "Try a different query or status filter."
              : "Run some research and save it as a decision to build your archive."}
          </p>
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-[17px] top-4 bottom-4 w-px bg-border/60" />
          <div className="space-y-4">
            {displayed.map((decision: any) => {
              const cfg = STATUS_CONFIG[decision.status] || STATUS_CONFIG.PROPOSED;
              return (
                <div
                  key={decision.id}
                  className="flex gap-4 group cursor-pointer"
                  onClick={() => router.push(`/workspaces/${workspaceId}/decisions/${decision.id}`)}
                >
                  <div className={cn(
                    "w-8 h-8 rounded-full border-2 shrink-0 flex items-center justify-center z-10 transition-colors",
                    "bg-background border-border group-hover:border-primary/50"
                  )}>
                    <div className={cn("w-2.5 h-2.5 rounded-full", {
                      "bg-yellow-500": decision.status === "PROPOSED",
                      "bg-green-500":  decision.status === "APPROVED",
                      "bg-blue-500":   decision.status === "IMPLEMENTED",
                      "bg-red-500":    decision.status === "REJECTED",
                      "bg-gray-400":   decision.status === "ARCHIVED",
                    })} />
                  </div>

                  <div className="flex-1 pb-2 min-w-0">
                    <div className="p-4 border border-border rounded-xl bg-surface group-hover:border-primary/30 transition-colors">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h3 className="text-sm font-medium text-foreground leading-snug">{decision.title}</h3>
                        <span className={cn("shrink-0 text-xs px-2 py-0.5 rounded-full border font-medium", cfg.color)}>
                          {cfg.label}
                        </span>
                      </div>
                      {decision.question && (
                        <p className="text-xs text-muted-foreground line-clamp-2">{decision.question}</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        {formatDistanceToNow(new Date(decision.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
