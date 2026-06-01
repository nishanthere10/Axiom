"use client";

import { Panel, Group, Separator } from "react-resizable-panels";

export default function DebugResizePage() {
  return (
    <div style={{ width: "100%", height: "100%" }}>
      <Group orientation="horizontal">
        <Panel id="left" defaultSize={30} minSize={10}>
          <div style={{ background: "#1e1e2e", height: "100%", padding: 16 }}>
            <h2 style={{ color: "#cdd6f4" }}>Left Panel</h2>
            <p style={{ color: "#a6adc8" }}>Try dragging the separator →</p>
          </div>
        </Panel>
        <Separator>
          <div style={{
            width: 6,
            height: "100%",
            background: "#45475a",
            cursor: "col-resize",
          }} />
        </Separator>
        <Panel id="center" defaultSize={40} minSize={10}>
          <div style={{ background: "#181825", height: "100%", padding: 16 }}>
            <h2 style={{ color: "#cdd6f4" }}>Center Panel</h2>
            <p style={{ color: "#a6adc8" }}>This is the center content area</p>
          </div>
        </Panel>
        <Separator>
          <div style={{
            width: 6,
            height: "100%",
            background: "#45475a",
            cursor: "col-resize",
          }} />
        </Separator>
        <Panel id="right" defaultSize={30} minSize={10}>
          <div style={{ background: "#1e1e2e", height: "100%", padding: 16 }}>
            <h2 style={{ color: "#cdd6f4" }}>Right Panel</h2>
            <p style={{ color: "#a6adc8" }}>← Try dragging the separator</p>
          </div>
        </Panel>
      </Group>
    </div>
  );
}
