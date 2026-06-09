"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { getSavedComparisons, SavedComparisonItem } from "@/lib/compare";

import ResizableLayout from "@/components/ui/ResizableLayout";

export default function SavedComparisonsPage() {
  const { getToken } = useAuth();
  const [comparisons, setComparisons] = useState<SavedComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadComparisons() {
      try {
        const token = await getToken() ?? "";
        const data = await getSavedComparisons(token);
        setComparisons(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load saved comparisons.");
      } finally {
        setLoading(false);
      }
    }
    
    loadComparisons();
  }, []);

  return (
    <ResizableLayout hideRightPanel>
      <div className="w-full space-y-8 animate-in fade-in duration-300">
        <div className="border-b border-border pb-4">
          <h1 className="text-2xl font-bold">Saved Comparisons</h1>
          <p className="text-sm text-muted-foreground mt-2">
            View your previously saved decision comparisons.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <p className="text-muted-foreground text-sm tracking-widest uppercase animate-pulse">
              Loading...
            </p>
          </div>
        ) : error ? (
          <p className="text-destructive text-sm text-center py-12">{error}</p>
        ) : comparisons.length === 0 ? (
          <p className="text-muted-foreground text-sm text-center py-12">
            No saved comparisons found.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {comparisons.map((comp) => (
              <Link 
                key={comp.id} 
                href={`/compare?id=${comp.id}`}
                className="block p-6 border border-border bg-card rounded-md hover:border-primary/50 transition-colors group"
              >
                <div className="flex flex-col h-full">
                  <h3 className="font-semibold text-lg line-clamp-2 group-hover:text-primary transition-colors">
                    {comp.summary}
                  </h3>
                  <div className="mt-4 space-y-1 text-xs font-mono text-muted-foreground line-clamp-2">
                    <p>A: {comp.session_a}</p>
                    <p>B: {comp.session_b}</p>
                  </div>
                  <div className="mt-auto pt-4 text-xs text-muted-foreground">
                    {new Date(comp.created_at).toLocaleDateString()}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </ResizableLayout>
  );
}
