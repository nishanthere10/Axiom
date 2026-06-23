"use client";

import { useCallback, useRef, useState, useEffect } from "react";
import { Suspense } from "react";
import { Menu, PanelRightClose } from "lucide-react";
import LeftSidebar from "./LeftSidebar";
import RightPanel from "./RightPanel";
import CenterCanvas from "./CenterCanvas";

interface ResizableLayoutProps {
  children: React.ReactNode;
  rightPanelContent?: React.ReactNode;
  rightPanelTitle?: string;
  hideRightPanel?: boolean;
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
      {/* Mobile Backdrop */}
      {isMobile && leftOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40" 
          onClick={toggleLeft} 
        />
      )}
      <aside
        className={`h-full shrink-0 bg-surface border-r border-border/50 overflow-hidden transition-all duration-300 ease-in-out ${isMobile ? 'fixed inset-y-0 left-0 z-50' : 'relative'}`}
        style={{ 
          width: isMobile ? '80vw' : (leftOpen ? SIDEBAR_OPEN_WIDTH : SIDEBAR_CLOSED_WIDTH),
          transform: isMobile && !leftOpen ? 'translateX(-100%)' : 'translateX(0)'
        }}
      >
        <Suspense fallback={null}>
          <LeftSidebar 
            isCollapsed={!isMobile && !leftOpen} 
            toggleCollapse={toggleLeft} 
            initialSessions={initialSessions}
            initialComparisons={initialComparisons}
          />
        </Suspense>
      </aside>



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
      {/* Mobile Backdrop */}
      {isMobile && rightOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40" 
          onClick={toggleRight} 
        />
      )}
      {!hideRightPanel && (
        <aside
          className={`h-full shrink-0 bg-surface border-l border-border/50 overflow-hidden transition-all duration-300 ease-in-out ${isMobile ? 'fixed inset-y-0 right-0 z-50' : 'relative'}`}
          style={{ 
            width: isMobile ? '85vw' : (rightOpen ? RIGHT_OPEN_WIDTH : RIGHT_CLOSED_WIDTH),
            transform: isMobile && !rightOpen ? 'translateX(100%)' : 'translateX(0)'
          }}
        >
          <RightPanel
            isCollapsed={!isMobile && !rightOpen}
            toggleCollapse={toggleRight}
            title={rightPanelTitle}
          >
            {rightPanelContent}
          </RightPanel>
        </aside>
      )}

    </div>
  );
}
