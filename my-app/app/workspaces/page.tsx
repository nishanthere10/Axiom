"use client";

import React, { useState, useMemo } from "react";
import { useWorkspace } from "@/components/WorkspaceContext";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { Plus, Trash2, Loader2, ArrowLeft, Users, Crown, Eye, UserCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { formatDistanceToNow } from "date-fns";
import { useToast } from "@/components/ui/ToastProvider";

function RoleBadge({ role }: { role?: string }) {
  if (!role || role === "owner") return null;
  const cfg = {
    member: { label: "Member", icon: UserCheck, cls: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
    viewer: { label: "Viewer", icon: Eye, cls: "bg-muted/60 text-muted-foreground border-border/60" },
  }[role] ?? { label: role, icon: Users, cls: "bg-muted/60 text-muted-foreground border-border/60" };
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full border ${cfg.cls}`}>
      <Icon size={9} />
      {cfg.label}
    </span>
  );
}

function WorkspaceCard({
  ws,
  activeWorkspaceId,
  onSetActive,
  onDelete,
  canDelete,
}: {
  ws: any;
  activeWorkspaceId: string | null;
  onSetActive: (id: string) => void;
  onDelete: (id: string) => void;
  canDelete: boolean;
}) {
  const isActive = activeWorkspaceId === ws.id;
  const isOwner = ws.user_role === "owner";

  return (
    <div
      className={`flex flex-col p-6 rounded-2xl border transition-all duration-300 shadow-sm group ${
        isActive
          ? "border-primary/50 bg-primary/5 shadow-[0_8px_24px_rgba(59,130,246,0.1)]"
          : "border-border/60 bg-surface/40 backdrop-blur-sm hover:border-border/80 hover:bg-surface/80 hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(0,0,0,0.12)]"
      }`}
    >
      <div className="flex justify-between items-start mb-2 gap-2">
        <h3 className="font-semibold text-lg text-foreground leading-snug">{ws.name}</h3>
        <div className="flex items-center gap-1.5 shrink-0">
          {isActive && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
              Active
            </span>
          )}
          {isOwner && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
              <Crown size={9} /> Owner
            </span>
          )}
          <RoleBadge role={ws.user_role} />
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2 leading-relaxed">
        {ws.description || "No description provided."}
      </p>

      {ws.created_at && (
        <p className="text-[11px] text-muted-foreground/60 font-mono mb-4" suppressHydrationWarning>
          Created {formatDistanceToNow(new Date(ws.created_at), { addSuffix: true })}
        </p>
      )}

      <div className="flex items-center gap-2 mt-auto pt-2">
        {!isActive ? (
          <button
            onClick={() => onSetActive(ws.id)}
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
        {isOwner && (
          <button
            onClick={() => onDelete(ws.id)}
            disabled={!canDelete}
            className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-colors disabled:opacity-50 disabled:pointer-events-none"
            title={!canDelete ? "Cannot delete the last workspace" : "Delete workspace"}
          >
            <Trash2 size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

export default function WorkspacesPage() {
  const { workspaces, isLoading, refreshWorkspaces, activeWorkspaceId, setActiveWorkspaceId } = useWorkspace();
  const { getToken } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Split into owned and shared
  const { ownedWorkspaces, sharedWorkspaces } = useMemo(() => {
    const owned = workspaces.filter((w) => !w.user_role || w.user_role === "owner");
    const shared = workspaces.filter((w) => w.user_role && w.user_role !== "owner");
    return { ownedWorkspaces: owned, sharedWorkspaces: shared };
  }, [workspaces]);

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
        getToken,
      });
      await refreshWorkspaces();
      setIsCreating(false);
      setNewName("");
      setNewDesc("");
      if (res && res.id) setActiveWorkspaceId(res.id);
      toast("Workspace created successfully", "success");
    } catch (err: any) {
      console.error(err);
      toast(err?.message || "Failed to create workspace", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTargetId) return;
    setDeleting(true);
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch(`/workspaces/${deleteTargetId}`, token, { method: "DELETE", getToken });
      if (activeWorkspaceId === deleteTargetId) setActiveWorkspaceId(null);
      await refreshWorkspaces();
      setDeleteTargetId(null);
      toast("Workspace deleted successfully", "success");
    } catch (err: any) {
      console.error(err);
      toast(err?.message || "Failed to delete workspace", "error");
    } finally {
      setDeleting(false);
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

      <div className="max-w-4xl mx-auto space-y-10">
        <div className="mb-10 text-center md:text-left">
          <button
            onClick={() => router.back()}
            className="text-sm font-medium text-muted-foreground hover:text-foreground mb-6 flex items-center gap-2 transition-colors px-2 py-1 rounded-md hover:bg-surface-hover w-fit"
          >
            <ArrowLeft size={16} /> Back
          </button>
          <h1 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground">Workspaces</h1>
          <p className="text-sm text-muted-foreground mt-2">Manage your team's workspaces and organization contexts.</p>
        </div>

        {/* Shared with me notification banner */}
        {sharedWorkspaces.length > 0 && (
          <div className="flex items-center gap-3 p-4 rounded-xl border border-blue-500/30 bg-blue-500/5 text-sm text-blue-400">
            <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center shrink-0">
              <Users size={14} className="text-blue-400" />
            </div>
            <p>
              You have been added to{" "}
              <span className="font-semibold text-foreground">
                {sharedWorkspaces.length} shared workspace{sharedWorkspaces.length > 1 ? "s" : ""}
              </span>
              . They appear below under <span className="font-semibold text-foreground">Shared with Me</span>.
            </p>
          </div>
        )}

        {/* My Workspaces */}
        <section>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
            <Crown size={12} className="text-amber-500" /> My Workspaces
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ownedWorkspaces.map((ws) => (
              <WorkspaceCard
                key={ws.id}
                ws={ws}
                activeWorkspaceId={activeWorkspaceId}
                onSetActive={setActiveWorkspaceId}
                onDelete={setDeleteTargetId}
                canDelete={ownedWorkspaces.length > 1}
              />
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
                    <label className="block text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 ml-1">
                      Workspace Name
                    </label>
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
                    <label className="block text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-1.5 ml-1">
                      Description (Optional)
                    </label>
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
        </section>

        {/* Shared with Me */}
        {sharedWorkspaces.length > 0 && (
          <section>
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
              <Users size={12} className="text-blue-400" /> Shared with Me
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sharedWorkspaces.map((ws) => (
                <WorkspaceCard
                  key={ws.id}
                  ws={ws}
                  activeWorkspaceId={activeWorkspaceId}
                  onSetActive={setActiveWorkspaceId}
                  onDelete={setDeleteTargetId}
                  canDelete={false}
                />
              ))}
            </div>
          </section>
        )}

        <ConfirmDialog
          isOpen={!!deleteTargetId}
          onClose={() => setDeleteTargetId(null)}
          onConfirm={confirmDelete}
          title="Delete Workspace?"
          description="Are you sure you want to delete this workspace? All associated research history and settings will be permanently removed."
          confirmText="Delete Workspace"
          isLoading={deleting}
        />
      </div>
    </div>
  );
}
