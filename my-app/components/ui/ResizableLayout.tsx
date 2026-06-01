"use client";

import { useRef, useState, useCallback } from "react";
import { Panel, Group, Separator } from "react-resizable-panels";
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

function DragHandle() {
  return (
    <div
      style={{
        width: 6,
        height: "100%",
        borderRadius: 3,
        backgroundColor: "rgba(255,255,255,0.08)",
        transition: "background-color 0.2s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.backgroundColor = "rgba(59,130,246,0.5)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.backgroundColor = "rgba(255,255,255,0.08)";
      }}
    />
  );
}

export default function ResizableLayout({ children, rightPanelContent, rightPanelTitle, hideRightPanel = false }: ResizableLayoutProps) {
  const leftPanelRef = useRef<PanelImperativeHandle>(null);
  const rightPanelRef = useRef<PanelImperativeHandle>(null);

  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  const toggleLeft = useCallback(() => {
    const panel = leftPanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  }, []);

  const toggleRight = useCallback(() => {
    const panel = rightPanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        panel.collapse();
      }
    }
  }, []);

  const handleLeftResize = useCallback((size: { asPercentage: number; inPixels: number }) => {
    setLeftCollapsed(size.asPercentage <= 5);
  }, []);

  const handleRightResize = useCallback((size: { asPercentage: number; inPixels: number }) => {
    setRightCollapsed(size.asPercentage <= 5);
  }, []);

  return (
    <Group orientation="horizontal" className="h-full w-full bg-background">
      <Panel
        id="atlas-left"
        panelRef={leftPanelRef}
        defaultSize={20}
        minSize={15}
        maxSize={30}
        collapsible
        collapsedSize={4}
        onResize={handleLeftResize}
        className="bg-[#171717] border-r border-border"
      >
        <LeftSidebar isCollapsed={leftCollapsed} toggleCollapse={toggleLeft} />
      </Panel>

      <Separator style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 1px", cursor: "col-resize" }}>
        <DragHandle />
      </Separator>

      <Panel id="atlas-center" defaultSize={hideRightPanel ? 76 : 56} minSize={30}>
        <CenterCanvas>{children}</CenterCanvas>
      </Panel>

      {!hideRightPanel && (
        <>
          <Separator style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "0 1px", cursor: "col-resize" }}>
            <DragHandle />
          </Separator>

          <Panel
            id="atlas-right"
            panelRef={rightPanelRef}
            defaultSize={20}
            minSize={15}
            maxSize={35}
            collapsible
            collapsedSize={4}
            onResize={handleRightResize}
            className="bg-[#171717] border-l border-border"
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
