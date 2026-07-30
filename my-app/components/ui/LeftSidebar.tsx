"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useWorkspace } from "@/components/WorkspaceContext";
import { WorkspaceSearchModal } from "@/components/workspaces/WorkspaceSearchModal";
import { cn } from "@/lib/utils";
import {
  Home,
  FlaskConical,
  BookMarked,
  FolderKanban,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
  Users,
  ChevronDown,
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type NavItem = {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: (workspaceId: string) => string;
  disabled?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  {
    id: "home",
    label: "Home",
    icon: <Home className="w-4 h-4" />,
    href: (id) => `/workspaces/${id}`,
  },
  {
    id: "research",
    label: "Research",
    icon: <FlaskConical className="w-4 h-4" />,
    href: (id) => `/workspaces/${id}/research`,
  },
  {
    id: "decisions",
    label: "Decisions",
    icon: <BookMarked className="w-4 h-4" />,
    href: (id) => `/workspaces/${id}/decisions`,
  },
  {
    id: "projects",
    label: "Projects",
    icon: <FolderKanban className="w-4 h-4" />,
    href: (id) => `/workspaces/${id}/projects`,
  },
];

export default function LeftSidebar({
  isCollapsed = false,
  toggleCollapse,
}: {
  isCollapsed?: boolean;
  toggleCollapse?: () => void;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { activeWorkspaceId, workspaces, setActiveWorkspaceId } = useWorkspace();
  const [searchOpen, setSearchOpen] = useState(false);
  const [sharedExpanded, setSharedExpanded] = useState(true);
  const [myExpanded, setMyExpanded] = useState(true);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const isActive = (item: NavItem) => {
    if (!activeWorkspaceId) return false;
    const href = item.href(activeWorkspaceId);
    if (item.id === "home") return pathname === href;
    return pathname.startsWith(href);
  };

  const myWorkspaces = useMemo(
    () => workspaces.filter((w) => !w.is_shared && !w.has_team_members && (!w.user_role || w.user_role === "owner")),
    [workspaces]
  );

  const sharedWorkspaces = useMemo(
    () => workspaces.filter((w) => w.is_shared || w.has_team_members || (w.user_role && w.user_role !== "owner")),
    [workspaces]
  );

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 border-b border-border/50 h-12 shrink-0">
        {!isCollapsed && (
          <span className="text-xs font-semibold text-muted-foreground tracking-widest uppercase select-none">
            Navigation
          </span>
        )}
        {toggleCollapse && (
          <button
            onClick={toggleCollapse}
            className={cn(
              "p-1.5 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none transition-colors shrink-0",
              isCollapsed && "mx-auto"
            )}
            aria-label="Toggle Sidebar"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        )}
      </div>

      <div className="px-2 pb-2 mt-2">
        <Tooltip delayDuration={100}>
          <TooltipTrigger asChild>
            <button
              onClick={() => setSearchOpen(true)}
              className={cn(
                "w-full flex items-center px-2.5 py-1.5 text-xs text-muted-foreground bg-surface border border-border/50 rounded-md hover:bg-surface-hover hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none transition-colors",
                isCollapsed ? "justify-center" : "justify-between"
              )}
            >
              <div className="flex items-center gap-2">
                <Search className="w-3.5 h-3.5 shrink-0" />
                {!isCollapsed && <span>Search...</span>}
              </div>
              {!isCollapsed && (
                <span className="font-mono text-[10px] bg-background px-1 rounded border border-border/50 shadow-sm shrink-0">
                  ⌘K
                </span>
              )}
            </button>
          </TooltipTrigger>
          {isCollapsed && <TooltipContent side="right"><p>Search (⌘K)</p></TooltipContent>}
        </Tooltip>
      </div>

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1 pt-1 border-t border-border/50">
        {NAV_ITEMS.map((item) => {
          const active = isActive(item);
          const href = activeWorkspaceId ? item.href(activeWorkspaceId) : "#";

          const btn = (
            <button
              key={item.id}
              disabled={item.disabled}
              onClick={() => !item.disabled && router.push(href)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-surface-hover hover:text-foreground",
                isCollapsed && "justify-center px-2 py-2",
                item.disabled && "opacity-40 cursor-not-allowed"
              )}
            >
              {item.icon}
              {!isCollapsed && <span className="truncate">{item.label}</span>}
              {!isCollapsed && item.disabled && (
                <span className="ml-auto text-[10px] text-muted-foreground font-mono bg-surface px-1 rounded">
                  soon
                </span>
              )}
            </button>
          );

          if (isCollapsed) {
            return (
              <Tooltip key={item.id} delayDuration={100}>
                <TooltipTrigger asChild>{btn}</TooltipTrigger>
                <TooltipContent side="right">
                  <p>{item.label}{item.disabled ? " (coming soon)" : ""}</p>
                </TooltipContent>
              </Tooltip>
            );
          }
          return btn;
        })}

        {/* My Workspaces section */}
        {myWorkspaces.length > 0 && (
          <div className="pt-2">
            {!isCollapsed ? (
              <>
                <button
                  onClick={() => setMyExpanded((v) => !v)}
                  className="w-full flex items-center justify-between px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-surface-hover group"
                >
                  <span className="flex items-center gap-1.5">
                    <FolderKanban className="w-3 h-3 text-primary" />
                    My Workspaces
                    <span className="text-[9px] font-bold bg-primary/10 text-primary px-1.5 py-0.5 rounded-full border border-primary/20">
                      {myWorkspaces.length}
                    </span>
                  </span>
                  <ChevronDown
                    className={cn(
                      "w-3 h-3 transition-transform",
                      myExpanded ? "rotate-0" : "-rotate-90"
                    )}
                  />
                </button>

                {myExpanded && (
                  <div className="mt-1 space-y-0.5 pl-1">
                    {myWorkspaces.map((ws) => {
                      const isActiveWs = ws.id === activeWorkspaceId;
                      return (
                        <button
                          key={ws.id}
                          onClick={() => {
                            setActiveWorkspaceId(ws.id);
                            router.push(`/workspaces/${ws.id}`);
                          }}
                          className={cn(
                            "w-full flex items-center gap-2 px-3 py-2 rounded-md transition-colors text-sm font-medium text-left",
                            isActiveWs
                              ? "bg-primary/10 text-primary"
                              : "text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                          )}
                        >
                          <div
                            className={cn(
                              "w-5 h-5 rounded-sm flex items-center justify-center text-[10px] font-bold shrink-0",
                              isActiveWs ? "bg-primary/20 text-primary" : "bg-surface text-muted-foreground border border-border/50"
                            )}
                          >
                            {ws.icon || ws.name.charAt(0).toUpperCase()}
                          </div>
                          <span className="truncate text-xs">{ws.name}</span>
                          <span className="ml-auto text-[9px] font-semibold uppercase tracking-wide text-primary/70 shrink-0">
                            Owner
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </>
            ) : (
              // Collapsed: show icon with badge
              <Tooltip delayDuration={100}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => router.push("/workspaces")}
                    className="w-full flex items-center justify-center px-2 py-2 rounded-md text-primary hover:bg-primary/10 transition-colors relative"
                  >
                    <FolderKanban className="w-4 h-4" />
                    <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-primary text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                      {myWorkspaces.length}
                    </span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>{myWorkspaces.length} My Workspace{myWorkspaces.length > 1 ? "s" : ""}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}

        {/* Shared Workspaces section */}
        {sharedWorkspaces.length > 0 && (
          <div className="pt-2">
            {!isCollapsed ? (
              <>
                <button
                  onClick={() => setSharedExpanded((v) => !v)}
                  className="w-full flex items-center justify-between px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-surface-hover group"
                >
                  <span className="flex items-center gap-1.5">
                    <Users className="w-3 h-3 text-blue-400" />
                    Shared Workspaces
                    <span className="text-[9px] font-bold bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">
                      {sharedWorkspaces.length}
                    </span>
                  </span>
                  <ChevronDown
                    className={cn(
                      "w-3 h-3 transition-transform",
                      sharedExpanded ? "rotate-0" : "-rotate-90"
                    )}
                  />
                </button>

                {sharedExpanded && (
                  <div className="mt-1 space-y-0.5 pl-1">
                    {sharedWorkspaces.map((ws) => {
                      const isActiveWs = ws.id === activeWorkspaceId;
                      return (
                        <button
                          key={ws.id}
                          onClick={() => {
                            setActiveWorkspaceId(ws.id);
                            router.push(`/workspaces/${ws.id}`);
                          }}
                          className={cn(
                            "w-full flex items-center gap-2 px-3 py-2 rounded-md transition-colors text-sm font-medium text-left",
                            isActiveWs
                              ? "bg-blue-500/10 text-blue-400"
                              : "text-muted-foreground hover:bg-surface-hover hover:text-foreground"
                          )}
                        >
                          <div
                            className={cn(
                              "w-5 h-5 rounded-sm flex items-center justify-center text-[10px] font-bold shrink-0",
                              isActiveWs ? "bg-blue-500/20 text-blue-400" : "bg-surface text-muted-foreground border border-border/50"
                            )}
                          >
                            {ws.icon || ws.name.charAt(0).toUpperCase()}
                          </div>
                          <span className="truncate text-xs">{ws.name}</span>
                          <span className="ml-auto text-[9px] font-semibold uppercase tracking-wide text-blue-400/70 shrink-0">
                            {ws.user_role}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </>
            ) : (
              // Collapsed: show icon with badge
              <Tooltip delayDuration={100}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => router.push("/workspaces")}
                    className="w-full flex items-center justify-center px-2 py-2 rounded-md text-blue-400 hover:bg-blue-500/10 transition-colors relative"
                  >
                    <Users className="w-4 h-4" />
                    <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-blue-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                      {sharedWorkspaces.length}
                    </span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>{sharedWorkspaces.length} Shared Workspace{sharedWorkspaces.length > 1 ? "s" : ""}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </div>

      {/* Settings footer */}
      <div className="px-2 py-2 border-t border-border/50 shrink-0">
        <Tooltip delayDuration={100}>
          <TooltipTrigger asChild>
            <button
              onClick={() => activeWorkspaceId && router.push(`/workspaces/${activeWorkspaceId}/settings`)}
              className={cn(
                "w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surface-hover focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none transition-colors text-muted-foreground hover:text-foreground text-xs font-medium",
                isCollapsed && "justify-center"
              )}
            >
              <Settings className="w-4 h-4 shrink-0" />
              {!isCollapsed && <span>Settings</span>}
            </button>
          </TooltipTrigger>
          {isCollapsed && <TooltipContent side="right"><p>Settings</p></TooltipContent>}
        </Tooltip>
      </div>

      {activeWorkspaceId && (
        <WorkspaceSearchModal
          workspaceId={activeWorkspaceId}
          isOpen={searchOpen}
          onClose={() => setSearchOpen(false)}
        />
      )}
    </div>
  );
}
