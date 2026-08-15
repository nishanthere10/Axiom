"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { Brain, X, ExternalLink, Trash2, Edit2, Check } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/ToastProvider";

interface MemoryItem {
  id: string;
  summary: string;
  memory_type: string;
  created_at: string;
  last_used_at?: string;
  relevance_score?: number;
  db?: { source_type?: string; source_id?: string };
}

interface Props {
  workspaceId: string;
  context?: string;   // current question — used for surface query
  isOpen: boolean;
  onClose: () => void;
}

export function MemorySidebar({ workspaceId, context, isOpen, onClose }: Props) {
  const { getToken } = useAuth();
  const { toast } = useToast();
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [activeTab, setActiveTab] = useState<"relevant" | "all">("relevant");

  const loadRelevant = useCallback(async () => {
    if (!context || !workspaceId) return;
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await apiFetch<{ memories: MemoryItem[] }>(
        `/workspaces/${workspaceId}/memory/surface?context=${encodeURIComponent(context)}&limit=8`,
        token, { getToken }
      );
      setMemories(data.memories || []);
    } catch (e) {
      console.error("Failed to load relevant memories", e);
    } finally {
      setLoading(false);
    }
  }, [context, workspaceId, getToken]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await apiFetch<{ memories: MemoryItem[] }>(
        `/workspaces/${workspaceId}/memory?limit=20`,
        token, { getToken }
      );
      setMemories(data.memories || []);
    } catch (e) {
      console.error("Failed to load memories", e);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, getToken]);

  useEffect(() => {
    if (!isOpen) return;
    if (activeTab === "relevant") loadRelevant();
    else loadAll();
  }, [isOpen, activeTab, loadRelevant, loadAll]);

  const handleDelete = async (id: string) => {
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch(`/workspaces/${workspaceId}/memory/${id}`, token, {
        method: "DELETE", getToken
      });
      setMemories(prev => prev.filter(m => m.id !== id));
      toast("Memory deleted", "success");
    } catch (e: any) {
      console.error("Failed to delete memory", e);
      toast(e?.message || "Failed to delete memory", "error");
    }
  };

  const handleEdit = async (id: string) => {
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch(`/workspaces/${workspaceId}/memory/${id}`, token, {
        method: "PATCH",
        body: JSON.stringify({ summary: editText }),
        getToken
      });
      setMemories(prev => prev.map(m => m.id === id ? { ...m, summary: editText } : m));
      setEditingId(null);
      toast("Memory updated", "success");
    } catch (e: any) {
      console.error("Failed to update memory", e);
      toast(e?.message || "Failed to update memory", "error");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-background border-l border-border shadow-2xl z-40 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary" />
          <span className="text-sm font-semibold">Axiom Memory</span>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border/50">
        {(["relevant", "all"] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "flex-1 py-2.5 text-xs font-medium transition-colors",
              activeTab === tab
                ? "text-primary border-b-2 border-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab === "relevant" ? "Relevant to this" : "All memories"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {loading ? (
          <div className="flex justify-center pt-8">
            <div className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-10">
            <Brain className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-40" />
            <p className="text-xs text-muted-foreground">
              {activeTab === "relevant"
                ? "No relevant memories found for this question."
                : "No memories yet. Research to build your knowledge archive."}
            </p>
          </div>
        ) : (
          memories.map(memory => (
            <div key={memory.id} className="p-3 border border-border rounded-lg bg-surface/50 space-y-2">
              {editingId === memory.id ? (
                <div className="space-y-2">
                  <textarea
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                    className="w-full text-xs bg-background border border-border rounded px-2 py-1.5 text-foreground resize-none focus:outline-none focus:ring-1 focus:ring-primary"
                    rows={4}
                  />
                  <div className="flex gap-2">
                    <button onClick={() => handleEdit(memory.id)}
                      className="flex items-center gap-1 text-xs text-primary hover:underline">
                      <Check className="w-3 h-3" /> Save
                    </button>
                    <button onClick={() => setEditingId(null)}
                      className="text-xs text-muted-foreground hover:text-foreground">Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-xs text-foreground leading-relaxed">{memory.summary}</p>
                  {memory.relevance_score !== undefined && (
                    <div className="flex items-center gap-1.5">
                      <div className="h-1 flex-1 bg-surface rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary/60 rounded-full"
                          style={{ width: `${Math.round(memory.relevance_score * 100)}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {Math.round(memory.relevance_score * 100)}%
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-muted-foreground capitalize">
                        {memory.memory_type} · {formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => { setEditingId(memory.id); setEditText(memory.summary); }}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleDelete(memory.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border/50">
        <a
          href={`/workspaces/${workspaceId}/memory`}
          className="text-xs text-primary hover:underline flex items-center gap-1"
        >
          <ExternalLink className="w-3 h-3" /> Browse all workspace memory
        </a>
      </div>
    </div>
  );
}
