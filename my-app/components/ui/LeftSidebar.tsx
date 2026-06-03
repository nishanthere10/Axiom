"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight, MessageSquare, Plus, Settings, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { getSessionHistory } from "@/lib/api";
import type { SessionHistoryItem } from "@/types";

export default function LeftSidebar({ isCollapsed = false, toggleCollapse }: { isCollapsed?: boolean, toggleCollapse?: () => void }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session_id");

  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function fetchHistory() {
      try {
        const data = await getSessionHistory();
        if (isMounted) setSessions(data.sessions);
      } catch (err) {
        console.error("Failed to fetch session history:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchHistory();
    return () => { isMounted = false; };
  }, []);

  const handleNewResearch = () => {
    router.push("/research");
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/research?session_id=${sessionId}`);
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border/50">
        {!isCollapsed && <h2 className="text-sm font-semibold text-foreground tracking-tight">History</h2>}
        {toggleCollapse && (
          <button
            onClick={toggleCollapse}
            className="p-1.5 rounded-md hover:bg-white/10 text-muted-foreground transition-colors mx-auto"
            aria-label="Toggle Sidebar"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <button
          onClick={handleNewResearch}
          className={cn(
            "w-full flex items-center gap-3 p-2 rounded-md hover:bg-white/10 transition-colors text-foreground text-sm font-medium mb-4",
            isCollapsed && "justify-center"
          )}
        >
          <Plus className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>New Research</span>}
        </button>

        {loading ? (
          // Loading skeleton
          !isCollapsed ? (
            <div className="space-y-2 px-1">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-9 bg-white/5 rounded-md animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="flex justify-center">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          )
        ) : sessions.length === 0 ? (
          !isCollapsed && (
            <p className="text-xs text-muted-foreground text-center px-2 py-4">
              No research sessions yet. Start your first one above!
            </p>
          )
        ) : (
          !isCollapsed ? (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => handleSessionClick(session.id)}
                className={cn(
                  "w-full flex items-center gap-3 p-2 rounded-md transition-colors text-sm text-left truncate",
                  activeSessionId === session.id
                    ? "bg-white/10 text-foreground"
                    : "hover:bg-white/5 text-muted-foreground hover:text-foreground"
                )}
              >
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="truncate">{session.question}</span>
              </button>
            ))
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => handleSessionClick(session.id)}
                className={cn(
                  "w-full flex justify-center p-2 rounded-md transition-colors",
                  activeSessionId === session.id
                    ? "bg-white/10 text-foreground"
                    : "hover:bg-white/5 text-muted-foreground hover:text-foreground"
                )}
                title={session.question}
              >
                <MessageSquare className="w-4 h-4 shrink-0" />
              </button>
            ))
          )
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
    </div>
  );
}
