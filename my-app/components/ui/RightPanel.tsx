"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function RightPanel({ children, title = "Auxiliary Data" }: { children: React.ReactNode, title?: string }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col border-l border-border bg-[#171717] transition-all duration-300 ease-in-out shrink-0",
        isCollapsed ? "w-12" : "w-80"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-border/50 h-[57px]">
        {!isCollapsed && <h2 className="text-sm font-semibold text-foreground tracking-tight truncate">{title}</h2>}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground transition-colors mx-auto"
          aria-label="Toggle Panel"
        >
          {isCollapsed ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>
      
      <div className={cn("flex-1 overflow-y-auto p-4 space-y-6", isCollapsed && "hidden")}>
        {children}
      </div>
    </aside>
  );
}
