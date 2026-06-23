"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/components/WorkspaceContext";
import { ChevronDown, Plus, Settings } from "lucide-react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

export default function WorkspaceSelector() {
  const { workspaces, activeWorkspaceId, setActiveWorkspaceId, isLoading } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  if (isLoading) {
    return <div className="h-8 w-32 animate-pulse bg-surface/50 rounded-md"></div>;
  }

  // 🛑 DEFENSIVE GUARD: Default to an empty array if context fails to provide one
  const safeWorkspaces = workspaces || [];
  const activeWorkspace = safeWorkspaces.find(w => w.id === activeWorkspaceId);

  return (
    <div className="relative z-50">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-surface transition-colors border border-surface/50 hover:border-surface"
      >
        <span className="text-sm font-medium text-text-primary truncate max-w-[120px]">
          {activeWorkspace?.name || "Select Workspace"}
        </span>
        <ChevronDown size={14} className="text-text-secondary" />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 w-56 rounded-xl bg-surface/90 backdrop-blur-md border border-border/60 shadow-[0_8px_30px_rgba(0,0,0,0.12)] py-1.5 left-0">
          <div className="px-3 py-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
            Workspaces
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {safeWorkspaces.map((ws) => (
              <button
                key={ws.id}
                onClick={() => {
                  setActiveWorkspaceId(ws.id);
                  setIsOpen(false);
                  if (pathname?.includes("/settings/integrations/github")) {
                    router.push(`/workspaces/${ws.id}`);
                  }
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-surface-hover transition-colors ${
                  activeWorkspaceId === ws.id ? "bg-primary/10 text-primary font-medium" : "text-foreground"
                }`}
              >
                <span className="truncate">{ws.name}</span>
                {activeWorkspaceId === ws.id && <span className="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>}
              </button>
            ))}
          </div>

          <div className="border-t border-border/50 mt-1.5 pt-1.5">
            <Link 
              href="/workspaces" 
              onClick={() => setIsOpen(false)}
              className="w-full text-left px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors flex items-center gap-2 font-medium"
            >
              <Settings size={14} />
              Manage Workspaces
            </Link>
          </div>
        </div>
      )}
      
      {/* Click outside backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-[-1]" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}
