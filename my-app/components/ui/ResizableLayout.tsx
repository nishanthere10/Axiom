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
const MIN_DRAG_WIDTH = 180;
const MAX_DRAG_WIDTH = 400;

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
  const [leftWidth,  setLeftWidth]  = useState(SIDEBAR_OPEN_WIDTH);
  const [rightWidth, setRightWidth] = useState(RIGHT_OPEN_WIDTH);
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

  const leftDragging  = useRef(false);
  const rightDragging = useRef(false);

  const toggleLeft  = useCallback(() => setLeftOpen(prev => !prev), []);
  const toggleRight = useCallback(() => setRightOpen(prev => !prev), []);

  /* ── Left drag handle ── */
  const onLeftMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    leftDragging.current = true;
    const startX = e.clientX;
    const startW = leftWidth;

    const onMove = (ev: MouseEvent) => {
      if (!leftDragging.current) return;
      const next = Math.min(MAX_DRAG_WIDTH, Math.max(MIN_DRAG_WIDTH, startW + ev.clientX - startX));
      setLeftWidth(next);
      if (!leftOpen) setLeftOpen(true);
    };
    const onUp = () => {
      leftDragging.current = false;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }, [leftWidth, leftOpen]);

  /* ── Right drag handle ── */
  const onRightMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    rightDragging.current = true;
    const startX = e.clientX;
    const startW = rightWidth;

    const onMove = (ev: MouseEvent) => {
      if (!rightDragging.current) return;
      const next = Math.min(MAX_DRAG_WIDTH, Math.max(MIN_DRAG_WIDTH, startW - (ev.clientX - startX)));
      setRightWidth(next);
      if (!rightOpen) setRightOpen(true);
    };
    const onUp = () => {
      rightDragging.current = false;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }, [rightWidth, rightOpen]);

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
          width: isMobile ? '80vw' : (leftOpen ? leftWidth : SIDEBAR_CLOSED_WIDTH),
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

      {/* Left drag handle */}
      {leftOpen && (
        <div
          onMouseDown={onLeftMouseDown}
          className="w-1 h-full shrink-0 cursor-col-resize hover:bg-primary/40 transition-colors duration-150 group"
          title="Drag to resize sidebar"
        >
          <div className="w-px h-full mx-auto bg-border group-hover:bg-primary/40 transition-colors" />
        </div>
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

      {/* Right drag handle */}
      {!hideRightPanel && rightOpen && (
        <div
          onMouseDown={onRightMouseDown}
          className="w-1 h-full shrink-0 cursor-col-resize hover:bg-primary/40 transition-colors duration-150 group"
          title="Drag to resize panel"
        >
          <div className="w-px h-full mx-auto bg-border group-hover:bg-primary/40 transition-colors" />
        </div>
      )}

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
            width: isMobile ? '85vw' : (rightOpen ? rightWidth : RIGHT_CLOSED_WIDTH),
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
