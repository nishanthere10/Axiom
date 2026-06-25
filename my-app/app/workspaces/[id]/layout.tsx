"use client";

import React, { createContext, useContext, useState, useEffect, use } from "react";
import ResizableLayout from "@/components/ui/ResizableLayout";
import { useWorkspace as useGlobalWorkspace } from "@/components/WorkspaceContext";

type RightPanelContextType = {
  setRightPanel: (title: string) => void;
  hideRightPanel: () => void;
};

const RightPanelContext = createContext<RightPanelContextType>({
  setRightPanel: () => {},
  hideRightPanel: () => {},
});

export function useRightPanel() {
  return useContext(RightPanelContext);
}

export default function WorkspaceLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ id: string }>;
}) {
  const unwrappedParams = use(params);
  const workspaceId = unwrappedParams.id;

  const [rightPanelTitle, setRightPanelTitle] = useState("Panel");
  const [isHidden, setIsHidden] = useState(true);
  
  const { setActiveWorkspaceId } = useGlobalWorkspace();

  useEffect(() => {
    // Sync the URL param with the global workspace context
    if (workspaceId) {
      setActiveWorkspaceId(workspaceId);
    }
  }, [workspaceId, setActiveWorkspaceId]);

  const setRightPanel = (title: string) => {
    setRightPanelTitle(title);
    setIsHidden(false);
  };

  const hideRightPanel = () => {
    setIsHidden(true);
  };

  return (
    <RightPanelContext.Provider value={{ setRightPanel, hideRightPanel }}>
      <ResizableLayout
        rightPanelTitle={rightPanelTitle}
        hideRightPanel={isHidden}
        rightPanelContent={<div id="right-panel-root" className="h-full w-full" />}
      >
        {children}
      </ResizableLayout>
    </RightPanelContext.Provider>
  );
}
