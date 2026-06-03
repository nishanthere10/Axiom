"use client";

import { useState, useCallback, Suspense } from "react";
import LeftSidebar from "./LeftSidebar";
import RightPanel from "./RightPanel";
import CenterCanvas from "./CenterCanvas";

interface ResizableLayoutProps {
  children: React.ReactNode;
  rightPanelContent?: React.ReactNode;
  rightPanelTitle?: string;
  hideRightPanel?: boolean;
}

export default function ResizableLayout({ children, rightPanelContent, rightPanelTitle, hideRightPanel = false }: ResizableLayoutProps) {
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);

  const toggleLeft = useCallback(() => setLeftOpen(prev => !prev), []);
  const toggleRight = useCallback(() => setRightOpen(prev => !prev), []);

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Left Sidebar */}
      <aside
        className="h-full shrink-0 bg-[#171717] border-r border-border/50 overflow-hidden transition-[width] duration-300 ease-in-out"
        style={{ width: leftOpen ? 260 : 48 }}
      >
        <Suspense fallback={null}>
          <LeftSidebar isCollapsed={!leftOpen} toggleCollapse={toggleLeft} />
        </Suspense>
      </aside>

      {/* Center Content */}
      <div className="flex-1 min-w-0 h-full overflow-hidden">
        <CenterCanvas>{children}</CenterCanvas>
      </div>

      {/* Right Panel */}
      {!hideRightPanel && (
        <aside
          className="h-full shrink-0 bg-[#171717] border-l border-border/50 overflow-hidden transition-[width] duration-300 ease-in-out"
          style={{ width: rightOpen ? 320 : 48 }}
        >
          <RightPanel isCollapsed={!rightOpen} toggleCollapse={toggleRight} title={rightPanelTitle}>
            {rightPanelContent}
          </RightPanel>
        </aside>
      )}
    </div>
  );
}
