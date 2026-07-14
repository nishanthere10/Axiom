"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Brain, Search, Download, Trash2, Edit2, Check, X, FileText, Settings2, Database, Zap } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { cn } from "@/lib/utils";

interface MemoryItem {
  id: string;
  summary: string;
  memory_type: string;
  created_at: string;
  scope: string;
  last_used_at?: string;
  source_type?: string;
}

export default function MemoryPanel() {
  const params = useParams();
  const workspaceId = params?.id as string;
  const { getToken } = useAuth();
  
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [stats, setStats] = useState<{total: number, by_type: Record<string, number>}>({total: 0, by_type: {}});
  const [loading, setLoading] = useState(true);
  
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const loadMemories = useCallback(async (query = "", type = "") => {
    if (!workspaceId) return;
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const data = await apiFetch<any>(
        `/workspaces/${workspaceId}/memory?limit=50&q=${encodeURIComponent(query)}&memory_type=${type}`,
        token, { getToken }
      );
      setMemories(data.memories || []);
      setStats({ total: data.total || 0, by_type: data.by_type || {} });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, getToken]);

  useEffect(() => {
    const delay = setTimeout(() => {
      loadMemories(q, typeFilter);
    }, 300);
    return () => clearTimeout(delay);
  }, [q, typeFilter, loadMemories]);

  const handleDelete = async (id: string) => {
    if (!confirm("Remove this memory? It will no longer influence the AI's context.")) return;
    try {
      const token = await getToken();
      await apiFetch(`/workspaces/${workspaceId}/memory/${id}`, token!, { method: "DELETE", getToken });
      setMemories(prev => prev.filter(m => m.id !== id));
      setStats(prev => ({ ...prev, total: prev.total - 1 }));
    } catch (e) {
      console.error(e);
    }
  };

  const handleEdit = async (id: string) => {
    try {
      const token = await getToken();
      await apiFetch(`/workspaces/${workspaceId}/memory/${id}`, token!, { 
        method: "PATCH", 
        body: JSON.stringify({ summary: editText }),
        getToken
      });
      setMemories(prev => prev.map(m => m.id === id ? { ...m, summary: editText } : m));
      setEditingId(null);
    } catch (e) {
      console.error(e);
    }
  };

  const handleExport = async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/workspaces/${workspaceId}/memory/export`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `atlas_memory_${workspaceId.substring(0,8)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.error("Export failed", e);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-6xl mx-auto py-8 px-4 md:px-8 space-y-8">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground flex items-center gap-2">
            <Brain className="w-6 h-6 text-primary" /> Workspace Memory
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            The AI automatically extracts and curates knowledge from your research sessions to build a persistent context graph.
          </p>
        </div>
        <button 
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-surface hover:bg-surface-hover text-foreground rounded-lg border border-border transition-colors whitespace-nowrap"
        >
          <Download className="w-3.5 h-3.5" /> Export Data
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-border/50 bg-surface/30">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Database className="w-4 h-4" /> <span className="text-xs font-medium uppercase tracking-wider">Total Nodes</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">{stats.total}</p>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-surface/30">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Settings2 className="w-4 h-4" /> <span className="text-xs font-medium uppercase tracking-wider">Decisions</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">{stats.by_type["decision"] || 0}</p>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-surface/30">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Zap className="w-4 h-4" /> <span className="text-xs font-medium uppercase tracking-wider">Preferences</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">{stats.by_type["preference"] || 0}</p>
        </div>
        <div className="p-4 rounded-xl border border-border/50 bg-surface/30">
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <FileText className="w-4 h-4" /> <span className="text-xs font-medium uppercase tracking-wider">Research</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">{stats.by_type["research"] || 0}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 items-center">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search memory..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
          />
        </div>
        <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 hide-scrollbar">
          {["", "decision", "preference", "research", "evidence"].map(t => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-full border transition-colors whitespace-nowrap",
                typeFilter === t 
                  ? "bg-primary text-primary-foreground border-primary" 
                  : "bg-surface text-muted-foreground border-border hover:text-foreground"
              )}
            >
              {t === "" ? "All" : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto space-y-3 pb-20">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-border rounded-xl">
            <Brain className="w-12 h-12 text-muted-foreground/30 mx-auto mb-4" />
            <h3 className="text-base font-medium text-foreground">No memories found</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Try adjusting your search or filters.
            </p>
          </div>
        ) : (
          memories.map((m) => (
            <div key={m.id} className="p-4 rounded-xl border border-border/50 bg-background/50 hover:bg-surface/30 transition-colors group">
              <div className="flex items-start justify-between gap-4">
                {editingId === m.id ? (
                  <div className="flex-1 space-y-3">
                    <textarea
                      value={editText}
                      onChange={e => setEditText(e.target.value)}
                      className="w-full text-sm bg-background border border-border rounded-lg px-3 py-2 text-foreground resize-none focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                      rows={4}
                    />
                    <div className="flex gap-2">
                      <button onClick={() => handleEdit(m.id)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md font-medium">
                        <Check className="w-3.5 h-3.5" /> Save Changes
                      </button>
                      <button onClick={() => setEditingId(null)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-surface text-foreground rounded-md font-medium hover:bg-surface-hover">
                        <X className="w-3.5 h-3.5" /> Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="flex-1 text-sm text-foreground leading-relaxed">
                    {m.summary}
                  </p>
                )}
                
                {editingId !== m.id && (
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <button onClick={() => { setEditingId(m.id); setEditText(m.summary); }} className="p-1.5 text-muted-foreground hover:text-foreground rounded-md hover:bg-surface">
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(m.id)} className="p-1.5 text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
              
              {editingId !== m.id && (
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border/30 text-[11px] text-muted-foreground font-mono uppercase tracking-wider">
                  <span className={cn(
                    "px-2 py-0.5 rounded-sm bg-surface font-semibold",
                    m.memory_type === 'decision' && "text-blue-500",
                    m.memory_type === 'preference' && "text-purple-500",
                    m.memory_type === 'evidence' && "text-amber-500"
                  )}>
                    {m.memory_type}
                  </span>
                  <span>Extracted {formatDistanceToNow(new Date(m.created_at), { addSuffix: true })}</span>
                  {m.last_used_at && (
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3 text-primary/70" /> Last surfaced {formatDistanceToNow(new Date(m.last_used_at), { addSuffix: true })}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
