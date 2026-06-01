"use client";

import { PreferenceInsight } from "@/lib/memory";

export default function PreferenceInsights({ insights }: { insights: PreferenceInsight[] }) {
  if (!insights || insights.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-muted-foreground border border-dashed border-border rounded-xl">
        No strong preferences detected yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {insights.map((insight, idx) => (
        <div key={idx} className="p-4 rounded-xl bg-primary/10 border border-primary/20 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">💡</span>
            <span className="font-semibold text-primary">{insight.value}</span>
          </div>
          <p className="text-sm text-foreground/80 pl-8">
            {insight.reason}
          </p>
        </div>
      ))}
    </div>
  );
}
