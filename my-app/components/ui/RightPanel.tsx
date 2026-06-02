"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface RightPanelProps {
  children: React.ReactNode;
  title?: string;
  isCollapsed?: boolean;
  toggleCollapse?: () => void;
}

export default function RightPanel({ children, title = "Auxiliary Data", isCollapsed = false, toggleCollapse }: RightPanelProps) {
  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border/50 h-[57px]">
        {!isCollapsed && <h2 className="text-sm font-semibold text-foreground tracking-tight truncate">{title}</h2>}
        {toggleCollapse && (
          <button
            onClick={toggleCollapse}
            className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground transition-colors mx-auto"
            aria-label="Toggle Panel"
          >
            {isCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        )}
      </div>
      
      <div className={cn("flex-1 overflow-y-auto p-4 space-y-6", isCollapsed && "hidden")}>
        {children}
      </div>
    </div>
  );
}
