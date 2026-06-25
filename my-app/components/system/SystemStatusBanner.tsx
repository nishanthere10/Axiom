"use client";

import { useState, useEffect, useRef } from "react";
import { AlertTriangle, X } from "lucide-react";

interface HealthStatus {
  status: "healthy" | "degraded" | "offline";
  services?: {
    postgres: boolean;
    pinecone: boolean;
  };
}

export function SystemStatusBanner() {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const prevStatusRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    let mounted = true;
    
    const checkHealth = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://atlas-1sr4.onrender.com";
        const res = await fetch(`${apiUrl}/health`);
        
        if (res.ok && mounted) {
          const data = await res.json() as HealthStatus;
          // If status changes from degraded or offline to healthy, reset dismissed state
          if ((prevStatusRef.current === "degraded" || prevStatusRef.current === "offline") && data.status === "healthy") {
            setDismissed(false);
          }
          prevStatusRef.current = data.status;
          setStatus(data);
        }
      } catch (err) {
        console.error("Health check failed:", err);
        if (mounted) {
          if (prevStatusRef.current !== "offline") {
            setDismissed(false);
          }
          prevStatusRef.current = "offline";
          setStatus({ status: "offline" });
        }
      }
      
      // Poll every 60 seconds
      if (mounted) {
        timeoutId = setTimeout(checkHealth, 60000);
      }
    };

    checkHealth();
    
    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, []); // No dependencies — runs once, self-schedules via setTimeout

  if (!status || status.status === "healthy" || dismissed) {
    return null;
  }

  // Determine specific messages
  const failedServices: string[] = [];
  if (status.services) {
    if (!status.services.postgres) failedServices.push("Database");
    if (!status.services.pinecone) failedServices.push("Memory System");
  }

  let message = "System performance is currently degraded. Some features may be unavailable or slow.";
  if (status.status === "offline") {
    message = "Backend server is currently offline or unreachable. Please try again later.";
  } else if (failedServices.length > 0) {
    message = `System degraded: ${failedServices.join(", ")} is currently unavailable.`;
  }

  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 text-amber-500 px-4 py-2 flex items-center justify-between text-sm z-50 relative">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4" />
        <span>{message}</span>
      </div>
      <button 
        onClick={() => setDismissed(true)}
        className="hover:bg-amber-500/20 p-1 rounded transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
