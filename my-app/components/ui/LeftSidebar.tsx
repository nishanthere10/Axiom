"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, MessageSquare, Plus, Settings, Loader2, GitCompare } from "lucide-react";
import { cn } from "@/lib/utils";
import { getSessionHistory, getSavedComparisons } from "@/lib/api";
import type { SessionHistoryItem, SavedComparisonItem } from "@/types";

const PAGE_SIZE = 10;

export default function LeftSidebar({ isCollapsed = false, toggleCollapse }: { isCollapsed?: boolean, toggleCollapse?: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session_id");
  const activeComparisonId = searchParams.get("comparison_id");

  const isCompareMode = pathname?.startsWith("/compare") ?? false;

  const [sessions, setSessions] = useState<SessionHistoryItem[]>([]);
  const [comparisons, setComparisons] = useState<SavedComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initial fetch
  useEffect(() => {
    let isMounted = true;
    async function fetchInitial() {
      setLoading(true);
      try {
        if (isCompareMode) {
          const data = await getSavedComparisons();
          if (isMounted) {
            setComparisons(data.comparisons);
            setHasMore(false); // /compare/saved doesn't have pagination yet
          }
        } else {
          const data = await getSessionHistory(PAGE_SIZE, 0);
          if (isMounted) {
            setSessions(data.sessions);
            setHasMore(data.sessions.length === PAGE_SIZE);
          }
        }
      } catch (err) {
        console.error("Failed to fetch sidebar history:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchInitial();
    return () => { isMounted = false; };
  }, [isCompareMode]);

  // Load more when scrolling to bottom (only for research mode right now)
  const loadMore = useCallback(async () => {
    if (isCompareMode || loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const data = await getSessionHistory(PAGE_SIZE, sessions.length);
      setSessions(prev => [...prev, ...data.sessions]);
      setHasMore(data.sessions.length === PAGE_SIZE);
    } catch (err) {
      console.error("Failed to load more sessions:", err);
    } finally {
      setLoadingMore(false);
    }
  }, [isCompareMode, loadingMore, hasMore, sessions.length]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el || !hasMore || loadingMore || isCompareMode) return;
    // Trigger load more when within 50px of the bottom
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
      loadMore();
    }
  }, [loadMore, hasMore, loadingMore, isCompareMode]);

  const handleNewAction = () => {
    if (isCompareMode) {
      router.push("/compare");
    } else {
      router.push("/research");
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/research?session_id=${sessionId}`);
  };

  const handleCompareClick = (compId: string) => {
    router.push(`/compare/saved?comparison_id=${compId}`);
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border/50">
        {!isCollapsed && <h2 className="text-sm font-semibold text-foreground tracking-tight">
          {isCompareMode ? "Compare History" : "History"}
        </h2>}
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

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-2 space-y-1"
      >
        <button
          onClick={handleNewAction}
          className={cn(
            "w-full flex items-center gap-3 p-2 rounded-md hover:bg-white/10 transition-colors text-foreground text-sm font-medium mb-4",
            isCollapsed && "justify-center"
          )}
        >
          <Plus className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>{isCompareMode ? "New Comparison" : "New Research"}</span>}
        </button>

        {loading ? (
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
        ) : isCompareMode ? (
          // COMPARE MODE RENDERING
          comparisons.length === 0 ? (
            !isCollapsed && (
              <p className="text-xs text-muted-foreground text-center px-2 py-4">
                No saved comparisons yet.
              </p>
            )
          ) : (
            <>
              {!isCollapsed ? (
                comparisons.map((comp) => (
                  <button
                    key={comp.id}
                    onClick={() => handleCompareClick(comp.id)}
                    className={cn(
                      "w-full flex items-center gap-3 p-2 rounded-md transition-colors text-sm text-left truncate",
                      activeComparisonId === comp.id
                        ? "bg-white/10 text-foreground"
                        : "hover:bg-white/5 text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <GitCompare className="w-4 h-4 shrink-0" />
                    <span className="truncate">{comp.summary}</span>
                  </button>
                ))
              ) : (
                comparisons.map((comp) => (
                  <button
                    key={comp.id}
                    onClick={() => handleCompareClick(comp.id)}
                    className={cn(
                      "w-full flex justify-center p-2 rounded-md transition-colors",
                      activeComparisonId === comp.id
                        ? "bg-white/10 text-foreground"
                        : "hover:bg-white/5 text-muted-foreground hover:text-foreground"
                    )}
                    title={comp.summary}
                  >
                    <GitCompare className="w-4 h-4 shrink-0" />
                  </button>
                ))
              )}
            </>
          )
        ) : (
          // RESEARCH MODE RENDERING
          sessions.length === 0 ? (
            !isCollapsed && (
              <p className="text-xs text-muted-foreground text-center px-2 py-4">
                No research sessions yet. Start your first one above!
              </p>
            )
          ) : (
            <>
              {!isCollapsed ? (
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
              )}

              {/* Load more indicator */}
              {loadingMore && (
                <div className="flex justify-center py-2">
                  <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                </div>
              )}
            </>
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
