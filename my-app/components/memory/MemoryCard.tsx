"use client";

import { MemoryItem } from "@/lib/memory";
import { useState } from "react";

interface Props {
  memory: MemoryItem;
  onPromoted?: (id: string) => void;
}

export default function MemoryCard({ memory, onPromoted }: Props) {
  const [promoting, setPromoting] = useState(false);

  const handlePromote = async () => {
    setPromoting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/memory/promote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ memory_id: memory.id }),
      });
      if (res.ok && onPromoted) {
        onPromoted(memory.id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setPromoting(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card shadow-sm space-y-3 relative group">
      <div className="flex justify-between items-start">
        <span className="text-[10px] uppercase tracking-widest font-semibold px-2 py-1 rounded bg-secondary text-secondary-foreground">
          {memory.memory_type}
        </span>
        <span className="text-xs text-muted-foreground">
          {memory.scope === "temporary" && memory.expires_at ? (
            `Expires ${new Date(memory.expires_at).toLocaleDateString()}`
          ) : (
            "Permanent"
          )}
        </span>
      </div>
      
      <p className="text-sm text-foreground leading-relaxed">
        {memory.summary}
      </p>

      {memory.scope === "temporary" && (
        <div className="pt-2 border-t border-border/50">
          <button
            onClick={handlePromote}
            disabled={promoting}
            className="text-xs font-semibold uppercase tracking-widest text-primary hover:text-primary/80 disabled:opacity-50 transition-colors"
          >
            {promoting ? "Promoting..." : "Save to Permanent Memory"}
          </button>
        </div>
      )}
    </div>
  );
}
