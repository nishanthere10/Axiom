"use client";

import { Panel, Group, Separator, usePanelRef } from "react-resizable-panels";
import { useEffect, useRef, useState } from "react";

export default function DebugResizePage() {
  const groupRef = useRef<HTMLDivElement>(null);
  const [log, setLog] = useState<string[]>([]);

  const addLog = (msg: string) => {
    setLog(prev => [...prev.slice(-20), `${new Date().toISOString().slice(11,19)} ${msg}`]);
  };

  useEffect(() => {
    // Check if the group element has the right children
    const timer = setTimeout(() => {
      const groupEl = document.querySelector("[data-group]");
      if (groupEl) {
        const children = Array.from(groupEl.children);
        const info = children.map((c, i) => {
          const el = c as HTMLElement;
          const hasPanel = el.hasAttribute("data-panel");
          const hasSep = el.hasAttribute("data-separator");
          const tag = el.tagName;
          const rect = el.getBoundingClientRect();
          return `  [${i}] ${tag} panel=${hasPanel} sep=${hasSep} w=${rect.width.toFixed(0)} h=${rect.height.toFixed(0)}`;
        });
        addLog(`Group children (${children.length}):`);
        info.forEach(l => addLog(l));

        // Check the group's own dimensions
        const groupRect = groupEl.getBoundingClientRect();
        addLog(`Group rect: ${groupRect.width.toFixed(0)}x${groupRect.height.toFixed(0)}`);
      } else {
        addLog("ERROR: No [data-group] element found!");
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Debug log overlay */}
      <div style={{
        position: "fixed", bottom: 0, right: 0, width: 500, maxHeight: 300,
        background: "rgba(0,0,0,0.9)", color: "#0f0", fontFamily: "monospace",
        fontSize: 11, padding: 8, zIndex: 9999, overflow: "auto",
        borderTop: "1px solid #333", borderLeft: "1px solid #333"
      }}>
        <strong style={{ color: "#ff0" }}>DEBUG LOG</strong>
        {log.map((l, i) => <div key={i}>{l}</div>)}
      </div>

      {/* The actual resizable panel test */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <Group orientation="horizontal">
          <Panel id="debug-left" defaultSize={30} minSize={10}>
            <div style={{ background: "#1e1e2e", height: "100%", padding: 16 }}>
              <h2 style={{ color: "#cdd6f4", fontSize: 18 }}>Left Panel</h2>
              <p style={{ color: "#a6adc8", fontSize: 14 }}>Drag the gray bar to the right →</p>
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

          <Panel id="debug-center" defaultSize={40} minSize={10}>
            <div style={{ background: "#181825", height: "100%", padding: 16 }}>
              <h2 style={{ color: "#cdd6f4", fontSize: 18 }}>Center Panel</h2>
              <p style={{ color: "#a6adc8", fontSize: 14 }}>Content area</p>
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

          <Panel id="debug-right" defaultSize={30} minSize={10}>
            <div style={{ background: "#1e1e2e", height: "100%", padding: 16 }}>
              <h2 style={{ color: "#cdd6f4", fontSize: 18 }}>Right Panel</h2>
              <p style={{ color: "#a6adc8", fontSize: 14 }}>← Drag the gray bar to the left</p>
            </div>
          </Panel>
        </Group>
      </div>
    </div>
  );
}
