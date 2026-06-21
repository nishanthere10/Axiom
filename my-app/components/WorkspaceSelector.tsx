"use client";

import React, { useState } from "react";
import { useWorkspace } from "@/components/WorkspaceContext";
import { ChevronDown, Plus, Settings } from "lucide-react";
import Link from "next/link";

export default function WorkspaceSelector() {
  const { workspaces, activeWorkspaceId, setActiveWorkspaceId, isLoading } = useWorkspace();
  const [isOpen, setIsOpen] = useState(false);

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
        <div className="absolute top-full mt-1 w-56 rounded-md bg-surface border border-surface/50 shadow-lg py-1 left-0">
          <div className="px-3 py-2 text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Workspaces
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {safeWorkspaces.map((ws) => (
              <button
                key={ws.id}
                onClick={() => {
                  setActiveWorkspaceId(ws.id);
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-white/5 transition-colors ${
                  activeWorkspaceId === ws.id ? "bg-accent/10 text-accent font-medium" : "text-text-primary"
                }`}
              >
                <span className="truncate">{ws.name}</span>
                {activeWorkspaceId === ws.id && <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>}
              </button>
            ))}
          </div>

          <div className="border-t border-surface/50 mt-1 pt-1">
            <Link 
              href="/workspaces" 
              onClick={() => setIsOpen(false)}
              className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-white/5 transition-colors flex items-center gap-2"
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
