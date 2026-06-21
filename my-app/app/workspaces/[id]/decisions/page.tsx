"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { DecisionRecord } from "@/types";
import { formatDistanceToNow } from "date-fns";

export default function DecisionsDashboard() {
  const params = useParams();
  const workspaceId = params.id as string;
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDecisions() {
      try {
        const res = await fetch("/api/decisions", {
          headers: {
            "x-workspace-id": workspaceId
          }
        });
        if (res.ok) {
          const data = await res.json();
          setDecisions(data.decisions);
        }
      } catch (e) {
        console.error("Failed to fetch decisions", e);
      } finally {
        setLoading(false);
      }
    }
    fetchDecisions();
  }, [workspaceId]);

  const updateStatus = async (decisionId: string, newStatus: string) => {
    try {
      const res = await fetch(`/api/decisions/${decisionId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        const updated = await res.json();
        setDecisions(prev => prev.map(d => d.id === decisionId ? updated : d));
      }
    } catch (e) {
      console.error("Failed to update status", e);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-light tracking-tight text-foreground">Decision Timeline</h1>
          <p className="text-muted-foreground mt-1">Track and manage architecture decisions within this workspace.</p>
        </div>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : decisions.length === 0 ? (
        <div className="text-center py-20 border border-border/50 rounded-xl bg-surface">
          <h3 className="text-lg font-medium text-foreground">No decisions yet</h3>
          <p className="text-sm text-muted-foreground mt-2">Run some research and save it as a decision to build your timeline.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {decisions.map(decision => (
            <div key={decision.id} className="p-6 rounded-xl border border-border bg-surface hover:border-primary/30 transition-colors">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                <div>
                  <h3 className="text-xl font-medium text-foreground">{decision.title}</h3>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                    <span>{formatDistanceToNow(new Date(decision.created_at), { addSuffix: true })}</span>
                    <span>•</span>
                    <span className="font-mono">{decision.id.substring(0, 8)}</span>
                  </div>
                </div>
                
                <select 
                  className="bg-background border border-border rounded-md px-3 py-1.5 text-sm focus:ring-1 focus:ring-primary outline-none"
                  value={decision.status}
                  onChange={(e) => updateStatus(decision.id, e.target.value)}
                >
                  <option value="PROPOSED">Proposed</option>
                  <option value="APPROVED">Approved</option>
                  <option value="IMPLEMENTED">Implemented</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ARCHIVED">Archived</option>
                </select>
              </div>
              
              <div className="bg-background/50 rounded-lg p-4 border border-border/50">
                <p className="text-sm text-muted-foreground mb-2"><strong>Question:</strong> {decision.question}</p>
                <div className="prose prose-sm dark:prose-invert max-w-none text-foreground/80 line-clamp-3">
                  {decision.recommendation_context}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
