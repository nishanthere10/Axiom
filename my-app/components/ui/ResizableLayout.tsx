"use client";

import { useCallback, useState, useEffect, Suspense } from "react";
import { Menu, PanelRightClose } from "lucide-react";
import LeftSidebar from "./LeftSidebar";
import RightPanel from "./RightPanel";
import CenterCanvas from "./CenterCanvas";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

import type { SessionHistoryItem, SavedComparisonItem } from "@/types";

interface ResizableLayoutProps {
  children: React.ReactNode;
  rightPanelContent?: React.ReactNode;
  rightPanelTitle?: string;
  hideRightPanel?: boolean;
  initialSessions?: SessionHistoryItem[];
  initialComparisons?: SavedComparisonItem[];
}

const SIDEBAR_OPEN_WIDTH  = 260;
const SIDEBAR_CLOSED_WIDTH = 48;
const RIGHT_OPEN_WIDTH    = 360;
const RIGHT_CLOSED_WIDTH  = 48;

export default function ResizableLayout({
  children,
  rightPanelContent,
  rightPanelTitle,
  hideRightPanel = false,
  initialSessions,
  initialComparisons,
}: ResizableLayoutProps) {
  const [leftOpen,  setLeftOpen]  = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setLeftOpen(false);
        setRightOpen(false);
      } else {
        setLeftOpen(true);
        setRightOpen(true);
      }
    };
    handleResize(); // Initial check
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const toggleLeft  = useCallback(() => setLeftOpen(prev => !prev), []);
  const toggleRight = useCallback(() => setRightOpen(prev => !prev), []);

  return (
    <div className="flex h-full w-full overflow-hidden select-none">

      {/* ── Left Sidebar ── */}
      {isMobile ? (
        <Sheet open={leftOpen} onOpenChange={setLeftOpen}>
          <SheetContent side="left" className="p-0 w-[80vw] bg-surface border-r border-border/50 sm:max-w-none">
            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
            <Suspense fallback={null}>
              <LeftSidebar 
                isCollapsed={false} 
                toggleCollapse={() => setLeftOpen(false)} 
                initialSessions={initialSessions}
                initialComparisons={initialComparisons}
              />
            </Suspense>
          </SheetContent>
        </Sheet>
      ) : (
        <aside
          className="h-full shrink-0 bg-surface border-r border-border/50 overflow-hidden transition-all duration-300 ease-in-out relative"
          style={{ width: leftOpen ? SIDEBAR_OPEN_WIDTH : SIDEBAR_CLOSED_WIDTH }}
        >
          <Suspense fallback={null}>
            <LeftSidebar 
              isCollapsed={!leftOpen} 
              toggleCollapse={toggleLeft} 
              initialSessions={initialSessions}
              initialComparisons={initialComparisons}
            />
          </Suspense>
        </aside>
      )}

      {/* ── Center Canvas ── */}
      <div className="flex-1 min-w-0 h-full overflow-hidden relative">
        <CenterCanvas>{children}</CenterCanvas>
        
        {/* Mobile Toggle Buttons */}
        {isMobile && !leftOpen && (
          <button 
            onClick={toggleLeft}
            className="absolute top-4 left-4 z-30 p-2.5 rounded-full bg-surface border border-white/10 shadow-xl text-foreground hover:bg-surface-hover"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        {isMobile && !hideRightPanel && !rightOpen && (
          <button 
            onClick={toggleRight}
            className="absolute top-4 right-4 z-30 p-2.5 rounded-full bg-surface border border-white/10 shadow-xl text-foreground hover:bg-surface-hover"
          >
            <PanelRightClose className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* ── Right Panel ── */}
      {!hideRightPanel && (
        isMobile ? (
          <Sheet open={rightOpen} onOpenChange={setRightOpen}>
            <SheetContent side="right" className="p-0 w-[85vw] bg-surface border-l border-border/50 sm:max-w-none">
              <SheetTitle className="sr-only">{rightPanelTitle || "Context Panel"}</SheetTitle>
              <RightPanel
                isCollapsed={false}
                toggleCollapse={() => setRightOpen(false)}
                title={rightPanelTitle}
              >
                {rightPanelContent}
              </RightPanel>
            </SheetContent>
          </Sheet>
        ) : (
          <aside
            className="h-full shrink-0 bg-surface border-l border-border/50 overflow-hidden transition-all duration-300 ease-in-out relative"
            style={{ width: rightOpen ? RIGHT_OPEN_WIDTH : RIGHT_CLOSED_WIDTH }}
          >
            <RightPanel
              isCollapsed={!rightOpen}
              toggleCollapse={toggleRight}
              title={rightPanelTitle}
            >
              {rightPanelContent}
            </RightPanel>
          </aside>
        )
      )}

    </div>
  );
}
