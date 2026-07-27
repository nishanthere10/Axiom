"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { User, Trash2, Shield, UserPlus, Mail } from "lucide-react";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useToast } from "@/components/ui/ToastProvider";
import { AccountIDBadge } from "@/components/ui/AccountIDBadge";

interface Member {
  id: string;
  user_id: string;
  role: string;
  created_at: string;
}

export function MembersList({ workspaceId }: { workspaceId: string }) {
  const { getToken, userId: currentUserId, isLoaded } = useAuth();
  const { toast } = useToast();
  
  const getTokenRef = useRef(getToken);
  useEffect(() => { getTokenRef.current = getToken; }, [getToken]);

  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [inviteUserId, setInviteUserId] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviting, setInviting] = useState(false);

  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadMembers = useCallback(async () => {
    if (!isLoaded || !workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const token = await getTokenRef.current();
      if (!token) {
        setLoading(false);
        return;
      }
      const data = await apiFetch<Member[]>(
        `/workspaces/${workspaceId}/members`,
        token, { getToken: getTokenRef.current }
      );
      setMembers(data || []);
    } catch (e: any) {
      console.error("Error loading members:", e);
      setError(e?.message || "Failed to load members.");
      setMembers([]);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, isLoaded]); // getToken via ref - stable reference, no loop

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteUserId.trim()) return;
    
    setInviting(true);
    try {
      const token = await getToken();
      const newMember = await apiFetch<Member>(`/workspaces/${workspaceId}/members`, token!, { 
        method: "POST", 
        body: JSON.stringify({ user_id: inviteUserId, role: inviteRole }),
        getToken 
      });
      setMembers(prev => [...prev, newMember]);
      setInviteUserId("");
      toast("Member invited successfully", "success");
    } catch (e: any) {
      console.error(e);
      toast(e?.message || "Failed to invite member. Are you an owner?", "error");
    } finally {
      setInviting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTargetId || !workspaceId) return;
    setDeleting(true);
    try {
      const token = await getToken();
      await apiFetch(`/workspaces/${workspaceId}/members/${deleteTargetId}`, token!, { method: "DELETE", getToken });
      setMembers(prev => prev.filter(m => m.user_id !== deleteTargetId));
      setDeleteTargetId(null);
      toast("Member removed", "success");
    } catch (e: any) {
      console.error(e);
      toast(e?.message || "Failed to remove member", "error");
    } finally {
      setDeleting(false);
    }
  };

  const isOwner = members.some(m => m.user_id === currentUserId && m.role === 'owner');

  return (
    <div className="space-y-8">
      <AccountIDBadge />

      {/* Invite Form */}
      {isOwner && (
        <div className="p-6 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm">
          <h2 className="text-lg font-medium text-foreground mb-4 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary" /> Invite New Member
          </h2>
          <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="User ID (e.g. user_2n...)"
                value={inviteUserId}
                onChange={(e) => setInviteUserId(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
                required
              />
            </div>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="py-2.5 px-4 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary text-foreground"
            >
              <option value="member">Member (Read/Write)</option>
              <option value="viewer">Viewer (Read Only)</option>
              <option value="owner">Owner (Admin)</option>
            </select>
            <button 
              type="submit" 
              disabled={inviting || !inviteUserId.trim()}
              className="px-6 py-2.5 bg-primary text-primary-foreground font-medium rounded-lg text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {inviting ? "Inviting..." : "Invite"}
            </button>
          </form>
        </div>
      )}

      {/* Members List */}
      <div className="rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-border/60 flex items-center justify-between">
          <h2 className="text-lg font-medium text-foreground">Current Members</h2>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-surface-hover text-muted-foreground border border-border/60">
            {members.length} Total
          </span>
        </div>
        
        <div className="divide-y divide-border/40">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            </div>
          ) : error ? (
            <div className="py-12 text-center text-destructive text-sm px-4">
              <p className="font-semibold mb-1">Could not load members</p>
              <p className="text-xs text-muted-foreground">{error}</p>
            </div>
          ) : members.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground text-sm">
              No members found.
            </div>
          ) : (
            members.map((m) => (
              <div key={m.id} className="p-4 sm:px-6 flex items-center justify-between hover:bg-surface/30 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-surface border border-border/60 flex items-center justify-center shrink-0">
                    <User className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground flex items-center gap-2">
                      {m.user_id} 
                      {m.user_id === currentUserId && <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded-sm bg-primary/10 text-primary font-bold">You</span>}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                      {m.role === 'owner' ? <Shield className="w-3 h-3 text-amber-500" /> : <User className="w-3 h-3" />}
                      <span className="capitalize">{m.role}</span>
                    </div>
                  </div>
                </div>
                
                {isOwner && m.user_id !== currentUserId && (
                  <button 
                    onClick={() => setDeleteTargetId(m.user_id)} 
                    className="p-2 text-muted-foreground hover:text-destructive rounded-md hover:bg-destructive/10 transition-colors"
                    title="Remove member"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={!!deleteTargetId}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={confirmDelete}
        title="Remove Member?"
        description="Are you sure you want to remove this user from the workspace? They will lose access immediately."
        confirmText="Remove Member"
        isLoading={deleting}
      />
    </div>
  );
}
