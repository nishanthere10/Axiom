"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface RightPanelProps {
  children: React.ReactNode;
  title?: string;
  isCollapsed?: boolean;
  toggleCollapse?: () => void;
}

export default function RightPanel({
  children,
  title = "Auxiliary Data",
  isCollapsed = false,
  toggleCollapse,
}: RightPanelProps) {
  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 border-b border-border/50 h-12 shrink-0">
        {!isCollapsed && (
          <h2 className="text-xs font-semibold text-muted-foreground tracking-widest uppercase truncate">
            {title}
          </h2>
        )}
        {toggleCollapse && (
          <button
            onClick={toggleCollapse}
            className={cn(
              "p-1.5 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors",
              isCollapsed && "mx-auto"
            )}
            aria-label="Toggle Panel"
          >
            {isCollapsed
              ? <ChevronLeft className="w-4 h-4" />
              : <ChevronRight className="w-4 h-4" />}
          </button>
        )}
      </div>

      {/* Content */}
      <div className={cn(
        "flex-1 overflow-y-auto px-4 py-5 space-y-6",
        isCollapsed && "hidden"
      )}>
        {children}
      </div>
    </div>
  );
}
