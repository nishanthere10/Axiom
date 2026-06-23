"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/components/WorkspaceContext";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { Plus, Trash2, Edit2, Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function WorkspacesPage() {
  const { workspaces, isLoading, refreshWorkspaces, activeWorkspaceId, setActiveWorkspaceId } = useWorkspace();
  const { getToken } = useAuth();
  const router = useRouter();

  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setSubmitting(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const res = await apiFetch<any>("/workspaces", token, {
        method: "POST",
        body: JSON.stringify({ name: newName, description: newDesc }),
        getToken
      });
      
      await refreshWorkspaces();
      setIsCreating(false);
      setNewName("");
      setNewDesc("");
      
      // Select the new workspace
      if (res && res.id) {
        setActiveWorkspaceId(res.id);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to create workspace");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this workspace?")) return;
    try {
      const token = await getToken();
      if (!token) return;
      
      await apiFetch(`/workspaces/${id}`, token, {
        method: "DELETE",
        getToken
      });
      
      if (activeWorkspaceId === id) {
        setActiveWorkspaceId(null);
      }
      
      await refreshWorkspaces();
    } catch (err) {
      console.error(err);
      alert("Failed to delete workspace");
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="animate-spin text-primary w-8 h-8" />
      </div>
    );
  }

  return (
    <div className="relative flex-1 overflow-y-auto bg-background p-6 md:p-12 min-h-screen">
      <div className="absolute inset-0 -z-10 flex items-center justify-center pointer-events-none">
        <div className="absolute w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px]" />
        <div className="absolute w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-[100px] translate-x-1/3 -translate-y-1/3" />
      </div>

      <div className="max-w-4xl mx-auto space-y-8">
        <div className="mb-10 text-center md:text-left">
          <button onClick={() => router.back()} className="text-sm font-medium text-muted-foreground hover:text-foreground mb-6 flex items-center gap-2 transition-colors px-2 py-1 rounded-md hover:bg-surface-hover w-fit">
            <ArrowLeft size={16} /> Back
          </button>
          <h1 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground">Workspaces</h1>
          <p className="text-sm text-muted-foreground mt-2">Manage your team's workspaces and organization contexts.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <div 
              key={ws.id} 
              className={`flex flex-col p-6 rounded-2xl border transition-all duration-300 shadow-sm group ${activeWorkspaceId === ws.id ? 'border-primary/50 bg-primary/5 shadow-[0_8px_24px_rgba(59,130,246,0.1)]' : 'border-border/60 bg-surface/40 backdrop-blur-sm hover:border-border/80 hover:bg-surface/80 hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(0,0,0,0.12)]'}`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg text-foreground">{ws.name}</h3>
                {activeWorkspaceId === ws.id && (
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                    Active
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mb-6 line-clamp-2 leading-relaxed">
                {ws.description || "No description provided."}
              </p>
              
              <div className="flex items-center gap-2 mt-auto pt-2">
                {activeWorkspaceId !== ws.id ? (
                  <button 
                    onClick={() => setActiveWorkspaceId(ws.id)}
                    className="text-xs font-medium px-4 py-2 rounded-xl bg-surface/60 border border-border/40 text-foreground hover:bg-surface hover:border-border/80 transition-colors"
                  >
                    Set Active
                  </button>
                ) : (
                  <div className="text-xs font-medium px-4 py-2 text-muted-foreground/80 border border-transparent">
                    Active Workspace
                  </div>
                )}
                
                <Link 
                  href={`/workspaces/${ws.id}`}
                  className="text-xs font-medium px-4 py-2 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-sm"
                >
                  Open
                </Link>

                <div className="flex-1" />
                <button 
                  onClick={() => handleDelete(ws.id)}
                  disabled={workspaces.length === 1}
                  className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-colors disabled:opacity-50 disabled:pointer-events-none"
                  title={workspaces.length === 1 ? "Cannot delete the last workspace" : "Delete workspace"}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}

          {!isCreating ? (
            <button 
              onClick={() => setIsCreating(true)}
              className="p-6 rounded-2xl border border-dashed border-border/60 bg-surface/20 backdrop-blur-sm hover:border-border hover:bg-surface/50 transition-all duration-300 flex flex-col items-center justify-center min-h-[180px] text-muted-foreground hover:text-foreground group"
            >
              <div className="w-12 h-12 rounded-full bg-surface/50 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 shadow-sm border border-border/40">
                <Plus size={20} />
              </div>
              <span className="font-medium text-sm">Create Workspace</span>
            </button>
          ) : (
            <div className="p-6 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm col-span-1 md:col-span-2 lg:col-span-1">
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 ml-1">Workspace Name</label>
                  <input 
                    type="text" 
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full bg-surface/50 border border-border/50 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all text-foreground placeholder:text-muted-foreground/60"
                    placeholder="e.g. Engineering Team"
                    autoFocus
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 ml-1">Description (Optional)</label>
                  <textarea 
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className="w-full bg-surface/50 border border-border/50 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/50 transition-all text-foreground placeholder:text-muted-foreground/60 resize-none h-16"
                    placeholder="What is this workspace for?"
                  />
                </div>
                <div className="flex items-center gap-3 pt-3">
                  <button 
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="flex-1 px-4 py-2.5 text-sm font-medium text-muted-foreground bg-surface/50 border border-border/40 hover:bg-surface hover:text-foreground rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={submitting || !newName.trim()}
                    className="flex-1 px-4 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-xl transition-all hover:bg-primary/90 disabled:opacity-50 shadow-sm"
                  >
                    {submitting ? "Creating..." : "Create"}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
