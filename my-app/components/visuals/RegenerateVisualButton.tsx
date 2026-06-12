"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { VisualSpec } from "@/lib/visuals";

interface Props {
  sessionId: string;
  onRegenerated: (visuals: VisualSpec[]) => void;
}

export default function RegenerateVisualButton({ sessionId, onRegenerated }: Props) {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRegenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken() ?? "";
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/research/regenerate-visuals`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      if (!res.ok) throw new Error("Failed to regenerate visuals");
      
      const data = await res.json();
      onRegenerated(data.visuals);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error regenerating");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-4 py-2 border-t border-border/50">
      <button
        onClick={handleRegenerate}
        disabled={loading}
        className="text-xs uppercase tracking-widest font-semibold text-muted-foreground hover:text-primary transition-colors disabled:opacity-50"
      >
        {loading ? "Generating..." : "Regenerate Visuals"}
      </button>
      {error && <span className="text-xs text-destructive">{error}</span>}
    </div>
  );
}
