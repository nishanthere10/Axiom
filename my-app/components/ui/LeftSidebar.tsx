"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Plus,
  Settings,
  GitCompare,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import { getSessionHistory, getSavedComparisons } from "@/lib/api";
import type { SessionHistoryItem, SavedComparisonItem } from "@/types";
import AnimatedList from "@/components/AnimatedList";
import Loader from "@/components/loader";

const PAGE_SIZE = 10;

/** Skeleton loader that mimics the shape of a history row */
function HistorySkeleton() {
  return (
    <div className="space-y-1 px-1 pt-1">
      {[80, 60, 90, 50, 75].map((w, i) => (
        <div
          key={i}
          className="h-8 rounded-md bg-surface-hover/60 animate-pulse"
          style={{ width: `${w}%` }}
        />
      ))}
    </div>
  );
}

export default function LeftSidebar({
  isCollapsed = false,
  toggleCollapse,
  initialSessions,
  initialComparisons,
}: {
  isCollapsed?: boolean;
  toggleCollapse?: () => void;
  initialSessions?: SessionHistoryItem[];
  initialComparisons?: SavedComparisonItem[];
}) {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const activeSessionId = searchParams.get("session_id");
  const activeComparisonId = searchParams.get("comparison_id");

  const isCompareMode = pathname?.startsWith("/compare") ?? false;

  const [sessions, setSessions] = useState<SessionHistoryItem[]>(initialSessions || []);
  const [comparisons, setComparisons] = useState<SavedComparisonItem[]>(initialComparisons || []);
  const [loading, setLoading] = useState(isCompareMode ? !initialComparisons : !initialSessions);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(isCompareMode ? false : (initialSessions ? initialSessions.length === PAGE_SIZE : true));
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initial fetch
  useEffect(() => {
    let isMounted = true;
    async function fetchInitial() {
      // Block the request until Clerk is fully initialized and authenticated
      if (!isLoaded || !isSignedIn) return;

      setLoading(true);
      try {
        const token = await getToken();

        // CRITICAL: Block literal string "null" or "undefined" that sometimes leak in Next.js
        if (!token || token === "null" || token === "undefined") {
          console.warn("Clerk provided an empty or invalid token string. Aborting fetch.");
          if (isMounted) { setComparisons([]); setSessions([]); setHasMore(false); }
          return;
        }

        // Log a truncated version to prove we have a real JWT (Format: eyJhb...)
        console.log("Valid JWT generated. Prefix:", token.substring(0, 15));
        if (isCompareMode) {
          if (initialComparisons) {
            if (isMounted) setLoading(false);
            return;
          }
          const data = await getSavedComparisons(token, getToken);
          if (isMounted) { setComparisons(data.comparisons); setHasMore(false); }
        } else {
          if (initialSessions) {
            if (isMounted) setLoading(false);
            return;
          }
          const data = await getSessionHistory(PAGE_SIZE, 0, token, getToken);
          if (isMounted) { setSessions(data.sessions); setHasMore(data.sessions.length === PAGE_SIZE); }
        }
      } catch (err) {
        console.error("Failed to fetch sidebar history:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchInitial();
    return () => { isMounted = false; };
  }, [isCompareMode, isLoaded, isSignedIn, getToken]);

  const loadMore = useCallback(async () => {
    if (isCompareMode || loadingMore || !hasMore) return;
    const token = await getToken();
    if (!token) return;
    setLoadingMore(true);
    try {
      const data = await getSessionHistory(PAGE_SIZE, sessions.length, token, getToken);
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
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) loadMore();
  }, [loadMore, hasMore, loadingMore, isCompareMode]);

  const handleNewAction = () => router.push(isCompareMode ? "/compare" : "/research");
  const handleSessionClick = (sessionId: string) => router.push(`/research?session_id=${sessionId}`);
  const handleCompareClick = (compId: string) => router.push(`/compare/saved?comparison_id=${compId}`);

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-3 border-b border-border/50 h-12 shrink-0">
        {!isCollapsed && (
          <span className="text-xs font-semibold text-muted-foreground tracking-widest uppercase select-none truncate min-w-0 pr-2">
            {isCompareMode ? "Compare History" : "History"}
          </span>
        )}
        {toggleCollapse && (
          <button
            onClick={toggleCollapse}
            className={cn(
              "p-1.5 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors shrink-0",
              isCollapsed && "mx-auto"
            )}
            aria-label="Toggle Sidebar"
          >
            {isCollapsed
              ? <ChevronRight className="w-4 h-4" />
              : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}
      </div>

      {/* Scrollable body */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-2 space-y-1"
      >
        {/* New action button */}
        <button
          onClick={handleNewAction}
          className={cn(
            "w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surface-hover transition-colors text-muted-foreground hover:text-foreground text-xs font-medium mb-2",
            isCollapsed && "justify-center"
          )}
        >
          <Plus className="w-4 h-4 shrink-0" />
          {!isCollapsed && (
            <span className="truncate min-w-0">{isCompareMode ? "New Comparison" : "New Research"}</span>
          )}
        </button>

        {/* Content */}
        {loading ? (
          !isCollapsed ? <HistorySkeleton /> : (
            <div className="flex justify-center pt-2">
              <div className="w-4 h-4 relative flex items-center justify-center overflow-hidden">
                <Loader scale={0.3} color="hsl(var(--muted-foreground))" />
              </div>
            </div>
          )
        ) : isCompareMode ? (
          comparisons.length === 0 ? (
            !isCollapsed && (
              <p className="text-xs text-muted-foreground text-center px-2 py-6">
                No saved comparisons yet.
              </p>
            )
          ) : (
            <AnimatedList
              className="!w-full !p-0 !max-w-none"
              innerClassName="overflow-visible p-0 flex flex-col gap-0.5"
              displayScrollbar={false}
              showGradients={false}
              items={comparisons.map(comp => ({
                id: comp.id,
                render: () => (
                  <div
                    className={cn(
                      "w-full flex items-center gap-2.5 px-2 py-2 rounded-md transition-colors text-xs text-left",
                      activeComparisonId === comp.id
                        ? "bg-surface-hover text-foreground"
                        : "text-muted-foreground hover:bg-surface-hover/60 hover:text-foreground",
                      isCollapsed && "justify-center"
                    )}
                    title={isCollapsed ? comp.summary : undefined}
                  >
                    <GitCompare className="w-4 h-4 shrink-0" />
                    {!isCollapsed && <span className="truncate">{comp.summary}</span>}
                  </div>
                ),
              }))}
              onItemSelect={(item) => handleCompareClick(item.id)}
            />
          )
        ) : (
          sessions.length === 0 ? (
            !isCollapsed && (
              <p className="text-xs text-muted-foreground text-center px-2 py-6">
                No research sessions yet.{" "}
                <button
                  onClick={handleNewAction}
                  className="text-primary underline underline-offset-2"
                >
                  Start one above.
                </button>
              </p>
            )
          ) : (
            <>
              <AnimatedList
                className="!w-full !p-0 !max-w-none"
                innerClassName="overflow-visible p-0 flex flex-col gap-0.5"
                displayScrollbar={false}
                showGradients={false}
                items={sessions.map(session => ({
                  id: session.id,
                  render: () => (
                    <div
                      className={cn(
                        "w-full flex items-center gap-2.5 px-2 py-2 rounded-md transition-colors text-xs text-left",
                        activeSessionId === session.id
                          ? "bg-surface-hover text-foreground"
                          : "text-muted-foreground hover:bg-surface-hover/60 hover:text-foreground",
                        isCollapsed && "justify-center"
                      )}
                      title={isCollapsed ? session.question : undefined}
                    >
                      <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                      {!isCollapsed && <span className="truncate">{session.question}</span>}
                    </div>
                  ),
                }))}
                onItemSelect={(item) => handleSessionClick(item.id)}
              />
              {loadingMore && (
                <div className="flex justify-center py-2">
                  <div className="w-4 h-4 relative flex items-center justify-center overflow-hidden">
                    <Loader scale={0.3} color="hsl(var(--muted-foreground))" />
                  </div>
                </div>
              )}
            </>
          )
        )}
      </div>

      {/* Footer: Settings */}
      <div className="px-2 py-2 border-t border-border/50 shrink-0">
        <button
          className={cn(
            "w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surface-hover transition-colors text-muted-foreground hover:text-foreground text-xs",
            isCollapsed && "justify-center"
          )}
        >
          <Settings className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>Settings</span>}
        </button>
      </div>

    </div>
  );
}
