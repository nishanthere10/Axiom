"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useWorkspace } from "@/components/WorkspaceContext";
import { createDecision } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md bg-surface border-border">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">Save as Decision</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Convert this research report into a tracked decision record.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-1">
            <label className="block text-sm font-medium">Decision Title</label>
            <input
              type="text"
              required
              className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          
          <div className="space-y-1">
            <label className="block text-sm font-medium">Initial Status</label>
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
          
          <DialogFooter className="pt-4 border-t border-border/50">
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
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
