"use client";

import { useWorkspace } from "@/components/WorkspaceContext";
import { ChevronDown, Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function WorkspaceSelector() {
  const { workspaces, activeWorkspaceId, setActiveWorkspaceId, isLoading } = useWorkspace();
  const router = useRouter();

  if (isLoading) {
    return <div className="h-8 w-32 animate-pulse bg-surface/50 rounded-md"></div>;
  }

  // 🛑 DEFENSIVE GUARD: Default to an empty array if context fails to provide one
  const safeWorkspaces = workspaces || [];
  const activeWorkspace = safeWorkspaces.find(w => w.id === activeWorkspaceId);

  const myWorkspaces = safeWorkspaces.filter(w => !w.is_shared && !w.has_team_members && (!w.user_role || w.user_role === "owner"));
  const sharedWorkspaces = safeWorkspaces.filter(w => w.is_shared || w.has_team_members || (w.user_role && w.user_role !== "owner"));

  return (
    <DropdownMenu>
      <DropdownMenuTrigger 
        aria-label="Select Workspace"
        className="group flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-surface transition-colors border border-surface/50 hover:border-surface outline-none"
      >
        <span className="text-sm font-medium text-text-primary truncate max-w-[120px]">
          {activeWorkspace?.name || "Select Workspace"}
        </span>
        <ChevronDown size={14} className="text-text-secondary transition-transform duration-200 group-data-[state=open]:rotate-180" />
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="start" className="w-56 max-h-72 overflow-y-auto rounded-xl bg-surface/90 backdrop-blur-md border border-border/60 shadow-[0_8px_30px_rgba(0,0,0,0.12)]">
        {myWorkspaces.length > 0 && (
          <>
            <DropdownMenuLabel className="px-3 py-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
              My Workspaces
            </DropdownMenuLabel>
            {myWorkspaces.map((ws) => (
              <DropdownMenuItem
                key={ws.id}
                onClick={() => {
                  setActiveWorkspaceId(ws.id);
                  router.push(`/workspaces/${ws.id}`);
                }}
                className={`w-full cursor-pointer px-3 py-2 text-sm flex items-center justify-between hover:bg-surface-hover focus:bg-surface-hover transition-colors ${
                  activeWorkspaceId === ws.id ? "bg-primary/10 text-primary font-medium" : "text-foreground"
                }`}
              >
                <span className="truncate">{ws.name}</span>
                {activeWorkspaceId === ws.id && <span className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>}
              </DropdownMenuItem>
            ))}
          </>
        )}

        {sharedWorkspaces.length > 0 && (
          <>
            {myWorkspaces.length > 0 && <DropdownMenuSeparator className="bg-border/50" />}
            <DropdownMenuLabel className="px-3 py-2 text-[10px] font-bold text-blue-400 uppercase tracking-widest flex items-center justify-between">
              <span>Shared with Me</span>
              <span className="text-[9px] bg-blue-500/10 px-1.5 py-0.5 rounded-full border border-blue-500/20">{sharedWorkspaces.length}</span>
            </DropdownMenuLabel>
            {sharedWorkspaces.map((ws) => (
              <DropdownMenuItem
                key={ws.id}
                onClick={() => {
                  setActiveWorkspaceId(ws.id);
                  router.push(`/workspaces/${ws.id}`);
                }}
                className={`w-full cursor-pointer px-3 py-2 text-sm flex items-center justify-between hover:bg-surface-hover focus:bg-surface-hover transition-colors ${
                  activeWorkspaceId === ws.id ? "bg-blue-500/10 text-blue-400 font-medium" : "text-foreground"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="truncate">{ws.name}</span>
                  <span className="text-[9px] uppercase font-semibold text-blue-400/70 bg-blue-500/10 px-1 py-0.2 rounded shrink-0">{ws.user_role}</span>
                </div>
                {activeWorkspaceId === ws.id && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.5)]"></span>}
              </DropdownMenuItem>
            ))}
          </>
        )}

        <DropdownMenuSeparator className="bg-border/50" />
        
        <DropdownMenuItem asChild>
          <Link 
            href="/workspaces" 
            className="w-full cursor-pointer text-sm text-muted-foreground hover:text-foreground focus:text-foreground hover:bg-surface-hover focus:bg-surface-hover transition-colors flex items-center gap-2 font-medium"
          >
            <Settings size={14} />
            Manage Workspaces
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

