"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import ResizableLayout from "@/components/ui/ResizableLayout";

type WorkspaceContextType = {
  setRightPanel: (title: string) => void;
  hideRightPanel: () => void;
};

const WorkspaceContext = createContext<WorkspaceContextType>({
  setRightPanel: () => {},
  hideRightPanel: () => {},
});

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [rightPanelTitle, setRightPanelTitle] = useState("Panel");
  const [isHidden, setIsHidden] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const setRightPanel = (title: string) => {
    setRightPanelTitle(title);
    setIsHidden(false);
  };

  const hideRightPanel = () => {
    setIsHidden(true);
  };

  return (
    <WorkspaceContext.Provider value={{ setRightPanel, hideRightPanel }}>
      <ResizableLayout
        rightPanelTitle={rightPanelTitle}
        hideRightPanel={isHidden}
        rightPanelContent={<div id="right-panel-root" className="h-full w-full" />}
      >
        {children}
      </ResizableLayout>
    </WorkspaceContext.Provider>
  );
}
