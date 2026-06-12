"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { AlertTriangle, X } from "lucide-react";

interface HealthStatus {
  status: "healthy" | "degraded";
  services?: {
    postgres: boolean;
    pinecone: boolean;
    groq: boolean;
    tavily: boolean;
  };
}

export function SystemStatusBanner() {
  const { getToken, isSignedIn } = useAuth();
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isSignedIn) return;

    let timeoutId: NodeJS.Timeout;
    
    const checkHealth = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${apiUrl}/admin/health`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        if (res.ok) {
          const data = await res.json() as HealthStatus;
          // If status changes from degraded to healthy, reset dismissed state
          if (status?.status === "degraded" && data.status === "healthy") {
            setDismissed(false);
          }
          setStatus(data);
        }
      } catch (err) {
        console.error("Health check failed:", err);
      }
      
      // Poll every 60 seconds
      timeoutId = setTimeout(checkHealth, 60000);
    };

    checkHealth();
    
    return () => clearTimeout(timeoutId);
  }, [isSignedIn, getToken, status?.status]);

  if (!status || status.status === "healthy" || dismissed) {
    return null;
  }

  // Determine specific messages
  const failedServices = [];
  if (status.services) {
    if (!status.services.postgres) failedServices.push("Database");
    if (!status.services.pinecone) failedServices.push("Memory System");
    if (!status.services.groq) failedServices.push("Primary AI Provider");
    if (!status.services.tavily) failedServices.push("Search Engine");
  }

  let message = "System performance is currently degraded. Some features may be unavailable or slow.";
  if (failedServices.length > 0) {
    message = `System degraded: ${failedServices.join(", ")} is currently unavailable.`;
    if (!status.services?.groq) {
        message += " Fallback AI providers activated.";
    }
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
