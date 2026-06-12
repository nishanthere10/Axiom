"use client";

import { useEffect, useState } from "react";
import { MemoryItem, PreferenceInsight } from "@/lib/memory";
import MemoryCard from "./MemoryCard";
import PreferenceInsights from "./PreferenceInsights";

export default function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMemories = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/memory`);
      if (res.ok) {
        const data = await res.json();
        setMemories(data?.memories || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handlePromoted = (id: string) => {
    setMemories(mems => 
      mems.map(m => m.id === id ? { ...m, scope: "permanent", expires_at: null } : m)
    );
  };

  const temporaryMemories = memories.filter(m => m.scope === "temporary");
  const permanentMemories = memories.filter(m => m.scope === "permanent");
  
  // For V1, we extract preference insights statically from preference memories if they exist
  // We can just mock a preference insight if a preference memory exists
  const preferenceMemories = memories.filter(m => m.memory_type === "preference");
  const insights: PreferenceInsight[] = preferenceMemories.map(m => ({
    type: "preference_candidate",
    value: m.metadata.value || m.summary,
    reason: m.metadata.reason || "Historical selection"
  }));

  if (loading) {
    return <div className="p-8 text-center text-sm text-muted-foreground animate-pulse">Loading Atlas Memory...</div>;
  }

  return (
    <div className="space-y-12 w-full max-w-4xl mx-auto py-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">Atlas Memory</h2>
        <p className="text-muted-foreground">Manage the architectural context and preferences Atlas uses to assist you.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-8">
          <section className="space-y-4">
            <h3 className="text-lg font-semibold border-b border-border pb-2">Permanent Memories</h3>
            {permanentMemories.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No permanent memories saved yet.</p>
            ) : (
              <div className="grid gap-4">
                {permanentMemories.map(m => <MemoryCard key={m.id} memory={m} />)}
              </div>
            )}
          </section>

          <section className="space-y-4">
            <div className="border-b border-border pb-2 flex justify-between items-end">
              <h3 className="text-lg font-semibold">Temporary Memories</h3>
              <span className="text-xs text-muted-foreground uppercase tracking-widest">30 Day TTL</span>
            </div>
            {temporaryMemories.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No recent temporary memories.</p>
            ) : (
              <div className="grid gap-4">
                {temporaryMemories.map(m => <MemoryCard key={m.id} memory={m} onPromoted={handlePromoted} />)}
              </div>
            )}
          </section>
        </div>

        <div className="md:col-span-1">
          <h3 className="text-lg font-semibold border-b border-border pb-2 mb-4">Learned Preferences</h3>
          <PreferenceInsights insights={insights} />
        </div>
      </div>
    </div>
  );
}
