"use client";

import React, { use, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { WorkspaceCommandCenter } from "@/components/workspaces/dashboard/WorkspaceCommandCenter";
import { Loader2 } from "lucide-react";

export default function WorkspaceDashboardPage({ params }: { params: Promise<{ id: string }> }) {
  const { getToken } = useAuth();
  const unwrappedParams = use(params);
  const workspaceId = unwrappedParams.id;
  
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      try {
        const token = await getToken();
        if (!token) return;

        const data = await apiFetch<any>(`/workspaces/${workspaceId}/dashboard`, token, { getToken });
        setDashboardData(data);
      } catch (err: any) {
        console.error("Failed to load dashboard", err);
        setError("Failed to load workspace dashboard.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [workspaceId, getToken]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="animate-spin text-primary w-8 h-8" />
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="flex h-full items-center justify-center text-red-500">
        {error || "Dashboard data not available."}
      </div>
    );
  }

  return <WorkspaceCommandCenter dashboardData={dashboardData} workspaceId={workspaceId} />;
}
