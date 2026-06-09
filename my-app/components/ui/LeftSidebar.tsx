"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, MessageSquare, Plus, Settings, Loader2, GitCompare } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import { getSessionHistory, getSavedComparisons } from "@/lib/api";
import type { SessionHistoryItem, SavedComparisonItem } from "@/types";
import AnimatedList from "@/components/AnimatedList";

const PAGE_SIZE = 10;

export default function LeftSidebar({ isCollapsed = false, toggleCollapse }: { isCollapsed?: boolean, toggleCollapse?: () => void }) {
  const { getToken } = useAuth();
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
        const token = await getToken();
        if (!token) {
          // If the user isn't signed in, don't attempt to fetch
          if (isMounted) {
            setComparisons([]);
            setSessions([]);
            setHasMore(false);
          }
          return;
        }

        if (isCompareMode) {
          const data = await getSavedComparisons(token);
          if (isMounted) {
            setComparisons(data.comparisons);
            setHasMore(false); // /compare/saved doesn't have pagination yet
          }
        } else {
          const data = await getSessionHistory(PAGE_SIZE, 0, token);
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
  }, [isCompareMode, getToken]);

  // Load more when scrolling to bottom (only for research mode right now)
  const loadMore = useCallback(async () => {
    if (isCompareMode || loadingMore || !hasMore) return;
    
    const token = await getToken();
    if (!token) return;

    setLoadingMore(true);
    try {
      const data = await getSessionHistory(PAGE_SIZE, sessions.length, token);
      setSessions(prev => [...prev, ...data.sessions]);
      setHasMore(data.sessions.length === PAGE_SIZE);
    } catch (err) {
      console.error("Failed to load more sessions:", err);
    } finally {
      setLoadingMore(false);
    }
  }, [isCompareMode, loadingMore, hasMore, sessions.length, getToken]);

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
            <AnimatedList
              className="!w-full !p-0 !max-w-none"
              innerClassName="overflow-visible p-0"
              displayScrollbar={false}
              showGradients={false}
              items={comparisons.map(comp => ({
                id: comp.id,
                render: () => (
                  <div
                    className={cn(
                      "w-full flex items-center gap-3 p-2 rounded-md transition-colors text-sm text-left truncate",
                      activeComparisonId === comp.id
                        ? "bg-white/10 text-foreground"
                        : "hover:bg-white/5 text-muted-foreground hover:text-foreground",
                      isCollapsed && "justify-center"
                    )}
                    title={isCollapsed ? comp.summary : undefined}
                  >
                    <GitCompare className="w-4 h-4 shrink-0" />
                    {!isCollapsed && <span className="truncate">{comp.summary}</span>}
                  </div>
                )
              }))}
              onItemSelect={(item) => handleCompareClick(item.id)}
            />
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
              <AnimatedList
                className="!w-full !p-0 !max-w-none"
                innerClassName="overflow-visible p-0 space-y-1"
                displayScrollbar={false}
                showGradients={false}
                items={sessions.map(session => ({
                  id: session.id,
                  render: () => (
                    <div
                      className={cn(
                        "w-full flex items-center gap-3 p-2 rounded-md transition-colors text-sm text-left truncate",
                        activeSessionId === session.id
                          ? "bg-white/10 text-foreground"
                          : "hover:bg-white/5 text-muted-foreground hover:text-foreground",
                        isCollapsed && "justify-center"
                      )}
                      title={isCollapsed ? session.question : undefined}
                    >
                      <MessageSquare className="w-4 h-4 shrink-0" />
                      {!isCollapsed && <span className="truncate">{session.question}</span>}
                    </div>
                  )
                }))}
                onItemSelect={(item) => handleSessionClick(item.id)}
              />

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
