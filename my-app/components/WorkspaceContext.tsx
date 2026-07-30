"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from "react";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";

type Workspace = {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  created_at?: string;
  user_role?: string; // "owner" | "member" | "viewer"
  user_id?: string;
  is_shared?: boolean;
  member_count?: number;
  has_team_members?: boolean;
};

interface WorkspaceContextType {
  activeWorkspaceId: string | null;
  setActiveWorkspaceId: (id: string | null) => void;
  workspaces: Workspace[];
  isLoading: boolean;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [activeWorkspaceId, setActiveWorkspaceIdState] = useState<string | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isLoaded, isSignedIn, getToken } = useAuth();

  const getTokenRef = useRef(getToken);
  useEffect(() => {
    getTokenRef.current = getToken;
  }, [getToken]);

  const refreshWorkspaces = useCallback(async () => {
    if (!isSignedIn) {
      setIsLoading(false);
      return;
    }
    try {
      const token = await getTokenRef.current();
      if (!token) {
        setIsLoading(false);
        return;
      }
      const res = await apiFetch<any>("/workspaces", token, { getToken: getTokenRef.current });
      
      // 🛑 DEFENSIVE GUARD: Ensure the expected data structure exists
      if (!res || !Array.isArray(res.workspaces)) {
        console.warn("Invalid or missing workspaces data from API.");
        setWorkspaces([]); // Fallback to empty array
        return;
      }

      // 🔐 FIX 5.1: Use user-scoped localStorage key to prevent cross-account pollution
      // Use first workspace's user_id as proxy (all workspaces belong to same user)
      const userId = res.workspaces[0]?.user_id || 'unknown';
      const storageKey = `activeWorkspaceId_${userId}`;
      
      const savedId = localStorage.getItem(storageKey);
      if (savedId && res.workspaces.some((w: Workspace) => w.id === savedId)) {
        setActiveWorkspaceIdState(savedId);
      } else if (res.workspaces.length > 0) {
        setActiveWorkspaceIdState(res.workspaces[0].id);
        localStorage.setItem(storageKey, res.workspaces[0].id);
        // Clean up old non-namespaced key if exists
        localStorage.removeItem("activeWorkspaceId");
      }
      setWorkspaces(res.workspaces);
    } catch (e) {
      console.error("Failed to fetch workspaces:", e);
      setWorkspaces([]); // Ensure UI doesn't crash on network failure
    } finally {
      setIsLoading(false);
    }
  }, [isSignedIn]);

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      refreshWorkspaces();
    } else if (isLoaded && !isSignedIn) {
      setIsLoading(false);
      setWorkspaces([]);
      setActiveWorkspaceIdState(null);
    }
  }, [isLoaded, isSignedIn, refreshWorkspaces]);

  // 🔐 FIX 5.1: Clear workspace state on sign-out to prevent cross-account pollution
  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      // User signed out → clear all workspace state
      localStorage.removeItem("activeWorkspaceId");
      // Also clear any user-scoped keys (we don't know the userId after signout, so clear pattern)
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith("activeWorkspaceId_")) {
          localStorage.removeItem(key);
        }
      });
      setActiveWorkspaceIdState(null);
      setWorkspaces([]);
      console.debug("Cleared workspace state on sign-out");
    }
  }, [isLoaded, isSignedIn]);

  const setActiveWorkspaceId = (id: string | null) => {
    setActiveWorkspaceIdState(id);
    
    // 🔐 FIX 5.1: Use user-scoped storage key
    const userId = workspaces[0]?.user_id || 'unknown';
    const storageKey = `activeWorkspaceId_${userId}`;
    
    if (id) {
      localStorage.setItem(storageKey, id);
      // Clean up old key
      localStorage.removeItem("activeWorkspaceId");
    } else {
      localStorage.removeItem(storageKey);
      localStorage.removeItem("activeWorkspaceId");
    }
  };

  return (
    <WorkspaceContext.Provider value={{ activeWorkspaceId, setActiveWorkspaceId, workspaces, isLoading, refreshWorkspaces }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
