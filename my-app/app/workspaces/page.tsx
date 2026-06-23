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
    <div className="flex-1 overflow-y-auto bg-background p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <button onClick={() => router.back()} className="text-sm text-text-secondary hover:text-text-primary mb-4 flex items-center gap-2">
            <ArrowLeft size={16} /> Back
          </button>
          <h1 className="text-3xl font-semibold tracking-tight text-text-primary">Workspaces</h1>
          <p className="text-text-secondary mt-1">Manage your team's workspaces and organization contexts.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <div 
              key={ws.id} 
              className={`p-5 rounded-xl border transition-all ${activeWorkspaceId === ws.id ? 'border-primary bg-primary/5' : 'border-surface bg-surface/50 hover:bg-surface'}`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-lg text-text-primary">{ws.name}</h3>
                {activeWorkspaceId === ws.id && (
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                    Active
                  </span>
                )}
              </div>
              <p className="text-sm text-text-secondary mb-6 line-clamp-2">
                {ws.description || "No description provided."}
              </p>
              
              <div className="flex items-center gap-2 mt-auto">
                {activeWorkspaceId !== ws.id ? (
                  <button 
                    onClick={() => setActiveWorkspaceId(ws.id)}
                    className="text-xs font-medium px-3 py-1.5 rounded-md bg-surface border border-surface/50 hover:bg-white/5 transition-colors"
                  >
                    Set Active
                  </button>
                ) : (
                  <div className="text-xs font-medium px-3 py-1.5 text-text-secondary">
                    Active
                  </div>
                )}
                
                <Link 
                  href={`/workspaces/${ws.id}`}
                  className="text-xs font-medium px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Open
                </Link>

                <div className="flex-1" />
                <button 
                  onClick={() => handleDelete(ws.id)}
                  disabled={workspaces.length === 1}
                  className="p-1.5 text-text-secondary hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors disabled:opacity-50 disabled:pointer-events-none"
                  title={workspaces.length === 1 ? "Cannot delete the last workspace" : "Delete workspace"}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          {!isCreating ? (
            <button 
              onClick={() => setIsCreating(true)}
              className="p-5 rounded-xl border border-dashed border-surface hover:border-surface-hover hover:bg-surface/30 transition-all flex flex-col items-center justify-center min-h-[160px] text-text-secondary hover:text-text-primary"
            >
              <Plus size={24} className="mb-2" />
              <span className="font-medium">Create Workspace</span>
            </button>
          ) : (
            <div className="p-5 rounded-xl border border-surface bg-surface/50 col-span-1 md:col-span-2 lg:col-span-1">
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">Workspace Name</label>
                  <input 
                    type="text" 
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="w-full bg-background border border-surface rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
                    placeholder="e.g. Engineering Team"
                    autoFocus
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1">Description (Optional)</label>
                  <textarea 
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className="w-full bg-background border border-surface rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary resize-none h-16"
                    placeholder="What is this workspace for?"
                  />
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <button 
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="flex-1 px-3 py-2 text-sm text-text-secondary hover:bg-white/5 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    disabled={submitting || !newName.trim()}
                    className="flex-1 px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md transition-colors hover:bg-primary/90 disabled:opacity-50"
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
