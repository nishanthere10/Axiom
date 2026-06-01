import { memo } from "react";
import type { DecisionDocument as DecisionDocumentType } from "@/types";
import EvidenceCard from "./EvidenceCard";
import EvidenceConsensus from "./EvidenceConsensus";
import RefreshEvidence from "./RefreshEvidence";
import VisualRenderer from "../visuals/VisualRenderer";
import RegenerateVisualButton from "../visuals/RegenerateVisualButton";
import MarkdownRenderer from "../ui/MarkdownRenderer";
import MemoryUsed from "../memory/MemoryUsed";

export const ConfidenceBar = memo(function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-mono">{pct}%</span>
      </div>
      <div className="h-1 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
});

const Section = memo(function Section({ title, content }: { title: string; content: string }) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        {title}
      </h3>
      <MarkdownRenderer content={content} />
    </div>
  );
});

interface Props {
  doc: DecisionDocumentType;
  sessionId: string;
  setDoc: (doc: DecisionDocumentType) => void;
}

export default function DecisionDocument({ doc, sessionId, setDoc }: Props) {
  return (
    <div id="decision-document" className="w-full space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="border-b border-border pb-4 space-y-1 flex justify-between items-start">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-widest">
            Decision Document · v{doc.version}
          </p>
          <h2 className="text-xl font-semibold text-foreground leading-snug">{doc.question}</h2>
        </div>
      </div>

      {/* Executive Summary */}
      <Section title="Executive Summary" content={doc.executive_summary} />

      {/* Memory Influence Transparency */}
      {doc.memory_context && (
        <MemoryUsed context={doc.memory_context} />
      )}

      {/* Recommendation */}
      <Section title="Recommendation" content={doc.recommendation_context} />

      {/* Visuals Section */}
      {doc.visuals && doc.visuals.length > 0 && (
        <div className="space-y-4 border-t border-border/50 pt-6 mt-6">
          <VisualRenderer visuals={doc.visuals} />
          <RegenerateVisualButton 
            sessionId={sessionId} 
            onRegenerated={(newVisuals) => setDoc({ ...doc, visuals: newVisuals, visuals_generated_at: new Date().toISOString() })}
          />
        </div>
      )}
      {(!doc.visuals || doc.visuals.length === 0) && (
        <div className="pt-2">
           <RegenerateVisualButton 
            sessionId={sessionId} 
            onRegenerated={(newVisuals) => setDoc({ ...doc, visuals: newVisuals, visuals_generated_at: new Date().toISOString() })}
          />
        </div>
      )}

      {/* Tradeoffs */}
      <Section title="Tradeoffs" content={doc.tradeoffs} />

      {/* Alternatives */}
      <Section title="Alternatives" content={doc.alternatives} />
    </div>
  );
}

export function AuxiliaryDocumentData({ doc, sessionId, onRefresh }: { doc: DecisionDocumentType, sessionId: string, onRefresh: (id: string) => void }) {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300">
      {/* Confidence */}
      <div className="space-y-3 rounded-md border border-border bg-card p-4">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Confidence Breakdown
        </h3>
        <ConfidenceBar label="Evidence Coverage" value={doc.confidence.evidence_coverage} />
        <ConfidenceBar label="Source Quality" value={doc.confidence.source_quality} />
        <ConfidenceBar label="Contradiction Risk" value={doc.confidence.contradiction_risk} />
        <ConfidenceBar label="Decision Confidence" value={doc.confidence.decision_confidence} />
      </div>

      {/* Evidence Section */}
      {doc.evidence && doc.evidence.length > 0 && (
        <div className="space-y-6">
          <EvidenceCard evidence={doc.evidence} />
          <EvidenceConsensus consensus={doc.consensus} />
        </div>
      )}

      <RefreshEvidence question={doc.question} onRefresh={onRefresh} />

      {/* Footer */}
      <p className="text-xs text-muted-foreground">
        Generated at {new Date(doc.created_at).toLocaleString()}
        {doc.evidence_generated_at && <br />}
        {doc.evidence_generated_at && `(Evidence: ${new Date(doc.evidence_generated_at).toLocaleString()})`}
      </p>
    </div>
  );
}
