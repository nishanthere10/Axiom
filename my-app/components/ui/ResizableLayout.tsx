"use client";

import { useRef, useState } from "react";
import { Panel, Group, Separator, useDefaultLayout } from "react-resizable-panels";
import type { PanelImperativeHandle } from "react-resizable-panels";
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
  const leftPanelRef = useRef<PanelImperativeHandle>(null);
  const rightPanelRef = useRef<PanelImperativeHandle>(null);

  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  // Robust, SSR-safe localStorage persistence layer
  const safeStorage = {
    getItem: (key: string) => {
      if (typeof window !== "undefined") {
        return localStorage.getItem(key);
      }
      return null;
    },
    setItem: (key: string, value: string) => {
      if (typeof window !== "undefined") {
        localStorage.setItem(key, value);
      }
    }
  };

  const { defaultLayout, onLayoutChanged } = useDefaultLayout({
    id: "atlas-layout",
    storage: safeStorage,
  });

  const toggleLeft = () => {
    const panel = leftPanelRef.current;
    if (panel) {
      if (leftCollapsed) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  };

  const toggleRight = () => {
    const panel = rightPanelRef.current;
    if (panel) {
      if (rightCollapsed) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  };

  return (
    <Group orientation="horizontal" defaultLayout={defaultLayout} onLayoutChanged={onLayoutChanged} className="flex h-full w-full bg-background overflow-hidden">
      <Panel
        ref={leftPanelRef}
        defaultSize={20}
        minSize={15}
        maxSize={30}
        collapsible
        collapsedSize={4}
        onCollapse={() => setLeftCollapsed(true)}
        onExpand={() => setLeftCollapsed(false)}
        className="transition-all duration-300 ease-in-out bg-[#171717] border-r border-border"
      >
        <LeftSidebar isCollapsed={leftCollapsed} toggleCollapse={toggleLeft} />
      </Panel>

      <Separator className="w-1 bg-border/50 hover:bg-primary/50 transition-colors cursor-col-resize active:bg-primary z-10" />

      <Panel defaultSize={hideRightPanel ? 80 : 60} minSize={30}>
        <CenterCanvas>{children}</CenterCanvas>
      </Panel>

      {!hideRightPanel && (
        <>
          <Separator className="w-1 bg-border/50 hover:bg-primary/50 transition-colors cursor-col-resize active:bg-primary z-10" />

          <Panel
            ref={rightPanelRef}
            defaultSize={20}
            minSize={15}
            maxSize={35}
            collapsible
            collapsedSize={4}
            onCollapse={() => setRightCollapsed(true)}
            onExpand={() => setRightCollapsed(false)}
            className="transition-all duration-300 ease-in-out bg-[#171717] border-l border-border"
          >
            <RightPanel isCollapsed={rightCollapsed} toggleCollapse={toggleRight} title={rightPanelTitle}>
              {rightPanelContent}
            </RightPanel>
          </Panel>
        </>
      )}
    </Group>
  );
}

