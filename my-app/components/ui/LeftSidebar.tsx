"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageSquare, Plus, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const mockSessions = [
  { id: "1", title: "PostgreSQL vs MongoDB" },
  { id: "2", title: "Next.js App Router caching" },
  { id: "3", title: "Redis pub/sub architecture" },
];

export default function LeftSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-[#171717] transition-all duration-300 ease-in-out shrink-0",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-border/50">
        {!isCollapsed && <h2 className="text-sm font-semibold text-foreground tracking-tight">History</h2>}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground transition-colors mx-auto"
          aria-label="Toggle Sidebar"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <button className={cn(
          "w-full flex items-center gap-3 p-2 rounded-md hover:bg-white/10 transition-colors text-foreground text-sm font-medium mb-4",
          isCollapsed && "justify-center"
        )}>
          <Plus className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>New Research</span>}
        </button>

        {!isCollapsed ? (
          mockSessions.map((session) => (
            <button
              key={session.id}
              className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground text-sm text-left truncate"
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="truncate">{session.title}</span>
            </button>
          ))
        ) : (
          mockSessions.map((session) => (
            <button
              key={session.id}
              className="w-full flex justify-center p-2 rounded-md hover:bg-white/5 transition-colors text-muted-foreground hover:text-foreground"
              title={session.title}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
            </button>
          ))
        )}
      </div>

      <div className="p-4 border-t border-border/50">
        <button className={cn(
          "w-full flex items-center gap-3 p-2 rounded-md hover:bg-white/10 transition-colors text-muted-foreground hover:text-foreground text-sm",
          isCollapsed && "justify-center"
        )}>
          <Settings className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  );
}
