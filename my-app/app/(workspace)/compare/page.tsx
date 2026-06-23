"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { submitComparison, getComparison, Comparison } from "@/lib/compare";
import SessionSelector from "@/components/compare/SessionSelector";
import ComparisonProgress from "@/components/compare/ComparisonProgress";
import VerdictBanner from "@/components/compare/VerdictBanner";
import KeyChangesTable from "@/components/compare/KeyChangesTable";
import DecisionEvolution from "@/components/compare/DecisionEvolution";
import ImpactSummary from "@/components/compare/ImpactSummary";
import SaveComparison from "@/components/compare/SaveComparison";
import StructuralDiff from "@/components/compare/StructuralDiff";
import MemoryUsed from "@/components/memory/MemoryUsed";

import VisualRenderer from "@/components/visuals/VisualRenderer";
import { createPortal } from "react-dom";
import { useWorkspace } from "../layout";
import ExportButton from "@/components/export/ExportButton";

function CompareContent() {
  const searchParams = useSearchParams();
  const { getToken } = useAuth();
  const idParam = searchParams.get("id");

  const [comparing, setComparing] = useState(false);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { setRightPanel, hideRightPanel } = useWorkspace();
  const [portalNode, setPortalNode] = useState<HTMLElement | null>(null);

  useEffect(() => {
    setRightPanel("Impact & Actions");
    setPortalNode(document.getElementById("right-panel-root"));
    return () => hideRightPanel();
  }, [setRightPanel, hideRightPanel]);

  useEffect(() => {
    if (idParam) {
      setComparing(true);
      setError(null);
      getToken().then(token => {
        getComparison(idParam, token ?? "")
          .then((data) => setComparison(data))
          .catch((err) => setError(err instanceof Error ? err.message : "Failed to load comparison."))
          .finally(() => setComparing(false));
      });
    }
  }, [idParam]);

  const handleCompare = async (sessionA: string, sessionB: string) => {
    setComparing(true);
    setError(null);
    setComparison(null);
    
    try {
      const token = await getToken() ?? "";
      const data = await submitComparison(sessionA, sessionB, token);
      setComparison(data.comparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setComparing(false);
    }
  };

  const rightPanelContent = (
    <>
      {comparison && (
        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300">
          <ImpactSummary impact={comparison.impact_summary} />
          
          <div className="pt-4 border-t border-border">
            <SaveComparison comparisonId={comparison.id} initialSaved={!!idParam} />
          </div>
        </div>
      )}
      {!comparison && (
        <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-2 opacity-50">
          <p className="text-sm text-muted-foreground font-medium">Awaiting Comparison</p>
          <p className="text-xs text-muted-foreground max-w-[200px]">
            Impact summaries will appear here.
          </p>
        </div>
      )}
    </>
  );

  return (
    <>
      {portalNode && createPortal(rightPanelContent, portalNode)}
      {!comparing && !comparison && (
        <div className="min-h-[50vh] flex flex-col justify-center">
          <SessionSelector onCompare={handleCompare} disabled={comparing} />
          {error && <p className="text-destructive text-sm text-center mt-4">{error}</p>}
        </div>
      )}

      {comparing && !comparison && (
        <div className="flex items-center justify-center min-h-[40vh]">
          <ComparisonProgress isComplete={false} />
        </div>
      )}

      {comparison && (
        <div className="w-full space-y-12 animate-in fade-in duration-300">
          <div className="border-b border-border pb-4 flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">Decision Comparison</h1>
              <p className="text-sm text-muted-foreground font-mono mt-2">
                A: {comparison.session_a} <br />
                B: {comparison.session_b}
              </p>
            </div>
            <div className="no-print">
              <ExportButton sessionId={comparison.id} sessionType="comparison" />
            </div>
          </div>

          {comparison.impact_summary?.memory_context && (
            <div className="mb-8">
              <MemoryUsed context={comparison.impact_summary.memory_context} />
            </div>
          )}

          <VerdictBanner verdict={comparison.decision_evolution?.verdict} />

          {comparison.visuals && comparison.visuals.length > 0 && (
            <div className="pt-4 border-t border-border/50">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground mb-4">Visual Comparison</h2>
              <VisualRenderer visuals={comparison.visuals} />
            </div>
          )}

          <div className="space-y-12">
            <KeyChangesTable changes={comparison.decision_evolution?.key_changes} />
            <DecisionEvolution evolution={comparison.decision_evolution} />
            <StructuralDiff diff={comparison.structural_diff} />
          </div>
          
          <div className="pt-12 border-t border-border flex justify-center no-print">
             <button 
                onClick={() => setComparison(null)}
                className="text-xs text-muted-foreground uppercase tracking-widest hover:text-foreground transition-colors"
             >
               Start New Comparison
             </button>
          </div>
        </div>
      )}
    </>
  );
}

import { Suspense } from "react";

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-muted-foreground text-sm tracking-widest uppercase animate-pulse">Loading...</div>}>
      <CompareContent />
    </Suspense>
  );
}
