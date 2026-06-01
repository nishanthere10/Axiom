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
    <Group orientation="horizontal">
      <Panel
        id="atlas-left"
        panelRef={leftPanelRef}
        defaultSize={20}
        minSize={15}
        maxSize={30}
        collapsible
        collapsedSize={4}
        onResize={handleLeftResize}
      >
        <div style={{ background: "#171717", height: "100%", borderRight: "1px solid var(--color-border, #262626)" }}>
          <LeftSidebar isCollapsed={leftCollapsed} toggleCollapse={toggleLeft} />
        </div>
      </Panel>

      <Separator>
        <div style={{
          width: 8,
          height: "100%",
          background: "#585b70",
          cursor: "col-resize",
          borderRadius: 4,
        }} />
      </Separator>

      <Panel id="atlas-center" defaultSize={hideRightPanel ? 76 : 56} minSize={30}>
        <CenterCanvas>{children}</CenterCanvas>
      </Panel>

      {!hideRightPanel && (
        <>
          <Separator>
            <div style={{
              width: 8,
              height: "100%",
              background: "#585b70",
              cursor: "col-resize",
              borderRadius: 4,
            }} />
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
          >
            <div style={{ background: "#171717", height: "100%", borderLeft: "1px solid var(--color-border, #262626)" }}>
              <RightPanel isCollapsed={rightCollapsed} toggleCollapse={toggleRight} title={rightPanelTitle}>
                {rightPanelContent}
              </RightPanel>
            </div>
          </Panel>
        </>
      )}
    </Group>
  );
}
