"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useWorkspace } from "@/components/WorkspaceContext";
import { createDecision } from "@/lib/api";

interface SaveDecisionModalProps {
  sessionId: string;
  defaultTitle: string;
  onClose: () => void;
  onSuccess: (decisionId: string) => void;
}

export default function SaveDecisionModal({ sessionId, defaultTitle, onClose, onSuccess }: SaveDecisionModalProps) {
  const [title, setTitle] = useState(defaultTitle || "New Decision");
  const [status, setStatus] = useState("PROPOSED");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { activeWorkspaceId } = useWorkspace();
  const { getToken } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("Authentication token not found");

      const created = await createDecision(
        {
          research_session_id: sessionId,
          title,
          status,
        },
        token,
        getToken
      );

      onSuccess(created.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-surface border border-border rounded-xl shadow-lg w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-2">Save as Decision</h2>
          <p className="text-sm text-muted-foreground mb-6">Convert this research report into a tracked decision record.</p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Decision Title</label>
              <input
                type="text"
                required
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Initial Status</label>
              <select
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="PROPOSED">Proposed</option>
                <option value="APPROVED">Approved</option>
                <option value="IMPLEMENTED">Implemented</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Approving this decision will permanently index it in the memory system.
              </p>
            </div>
            
            {error && <p className="text-sm text-destructive font-medium">{error}</p>}
            
            <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                disabled={loading}
              >
                {loading ? "Saving..." : "Save Decision"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
