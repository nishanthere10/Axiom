"use client";

import { useState } from "react";
import { saveComparison } from "@/lib/compare";

export default function SaveComparison({ comparisonId, initialSaved = false }: { comparisonId: string, initialSaved?: boolean }) {
  const [saved, setSaved] = useState(initialSaved);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      const success = await saveComparison(comparisonId);
      if (success) {
        setSaved(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save.");
    } finally {
      setLoading(false);
    }
  };

  if (saved) {
    return (
      <div className="flex justify-end pt-4">
        <span className="text-sm text-muted-foreground uppercase tracking-widest font-semibold flex items-center gap-2">
          <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Saved to Library
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-2 pt-4">
      {error && <span className="text-xs text-destructive">{error}</span>}
      <button
        onClick={handleSave}
        disabled={loading}
        className="px-6 py-2 bg-primary text-primary-foreground text-sm font-semibold uppercase tracking-widest hover:bg-primary/90 transition-colors disabled:opacity-50"
      >
        {loading ? "Saving..." : "Save Comparison"}
      </button>
    </div>
  );
}
