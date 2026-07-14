"use client";

import { useState, useEffect } from "react";
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
  const { activeWorkspaceId } = useWorkspace();
  const [searchOpen, setSearchOpen] = useState(false);

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
              "p-1.5 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground transition-colors shrink-0",
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
                "w-full flex items-center px-2.5 py-1.5 text-xs text-muted-foreground bg-surface border border-border/50 rounded-md hover:bg-surface-hover hover:text-foreground transition-colors",
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
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium",
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
      </div>

      {/* Settings footer */}
      <div className="px-2 py-2 border-t border-border/50 shrink-0">
        <Tooltip delayDuration={100}>
          <TooltipTrigger asChild>
            <button
              onClick={() => activeWorkspaceId && router.push(`/workspaces/${activeWorkspaceId}/settings`)}
              className={cn(
                "w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surface-hover transition-colors text-muted-foreground hover:text-foreground text-xs font-medium",
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
