"use client";

import { useCallback, useRef, useState } from "react";
import { Suspense } from "react";
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
}: ResizableLayoutProps) {
  const [leftOpen,  setLeftOpen]  = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [leftWidth,  setLeftWidth]  = useState(SIDEBAR_OPEN_WIDTH);
  const [rightWidth, setRightWidth] = useState(RIGHT_OPEN_WIDTH);

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
      <aside
        className="h-full shrink-0 bg-surface border-r border-border/50 overflow-hidden transition-[width] duration-300 ease-in-out"
        style={{ width: leftOpen ? leftWidth : SIDEBAR_CLOSED_WIDTH }}
      >
        <Suspense fallback={null}>
          <LeftSidebar isCollapsed={!leftOpen} toggleCollapse={toggleLeft} />
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
      <div className="flex-1 min-w-0 h-full overflow-hidden">
        <CenterCanvas>{children}</CenterCanvas>
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
      {!hideRightPanel && (
        <aside
          className="h-full shrink-0 bg-surface border-l border-border/50 overflow-hidden transition-[width] duration-300 ease-in-out"
          style={{ width: rightOpen ? rightWidth : RIGHT_CLOSED_WIDTH }}
        >
          <RightPanel
            isCollapsed={!rightOpen}
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
