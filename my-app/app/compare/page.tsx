"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { submitComparison, getComparison, Comparison } from "@/lib/compare";
import SessionSelector from "@/components/compare/SessionSelector";
import ComparisonProgress from "@/components/compare/ComparisonProgress";
import VerdictBanner from "@/components/compare/VerdictBanner";
import KeyChangesTable from "@/components/compare/KeyChangesTable";
import DecisionEvolution from "@/components/compare/DecisionEvolution";
import ImpactSummary from "@/components/compare/ImpactSummary";
import SaveComparison from "@/components/compare/SaveComparison";
import StructuralDiff from "@/components/compare/StructuralDiff";

function CompareContent() {
  const searchParams = useSearchParams();
  const idParam = searchParams.get("id");

  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (idParam) {
      setComparing(true);
      setError(null);
      getComparison(idParam)
        .then((data) => setComparison(data))
        .catch((err) => setError(err instanceof Error ? err.message : "Failed to load comparison."))
        .finally(() => setComparing(false));
    }
  }, [idParam]);

  const handleCompare = async (sessionA: string, sessionB: string) => {
    setComparing(true);
    setError(null);
    setComparison(null);
    
    try {
      const data = await submitComparison(sessionA, sessionB);
      setComparison(data.comparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setComparing(false);
    }
  };

  return (
    <main className="min-h-screen bg-background p-6 md:p-12 lg:p-24 selection:bg-primary/30">
      {!comparing && !comparison && (
        <>
          <SessionSelector onCompare={handleCompare} disabled={comparing} />
          {error && <p className="text-destructive text-sm text-center mt-4">{error}</p>}
        </>
      )}

      {comparing && !comparison && (
        <div className="flex items-center justify-center min-h-[40vh]">
          <ComparisonProgress isComplete={false} />
        </div>
      )}

      {comparison && (
        <div className="w-full max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
          <div className="border-b border-border pb-4">
            <h1 className="text-2xl font-bold">Decision Comparison</h1>
            <p className="text-sm text-muted-foreground font-mono mt-2">
              A: {comparison.session_a} <br />
              B: {comparison.session_b}
            </p>
          </div>

          <VerdictBanner verdict={comparison.decision_evolution?.verdict} />

          <div className="space-y-12">
            <KeyChangesTable changes={comparison.decision_evolution?.key_changes} />
            <ImpactSummary impact={comparison.impact_summary} />
            <DecisionEvolution evolution={comparison.decision_evolution} />
            <StructuralDiff diff={comparison.structural_diff} />
            
            <div className="flex justify-end pt-4 border-t border-border">
              <SaveComparison comparisonId={comparison.id} initialSaved={!!idParam} />
            </div>
          </div>
          
          <div className="pt-12 border-t border-border flex justify-center">
             <button 
                onClick={() => setComparison(null)}
                className="text-xs text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors"
             >
               Start New Comparison
             </button>
          </div>
        </div>
      )}
    </main>
  );
}

import { Suspense } from "react";

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background p-6 flex justify-center text-muted-foreground text-sm tracking-widest uppercase animate-pulse">Loading...</div>}>
      <CompareContent />
    </Suspense>
  );
}
