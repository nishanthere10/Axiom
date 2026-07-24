import { memo } from "react";
import { motion } from "framer-motion";
import type { DecisionDocument as DecisionDocumentType } from "@/types";
import EvidenceCard from "./EvidenceCard";
import EvidenceConsensus from "./EvidenceConsensus";
import RefreshEvidence from "./RefreshEvidence";
import VisualRenderer from "../visuals/VisualRenderer";
import RegenerateVisualButton from "../visuals/RegenerateVisualButton";
import MarkdownRenderer from "../ui/MarkdownRenderer";
import MemoryUsed from "../memory/MemoryUsed";

export const ConfidenceBar = memo(function ConfidenceBar({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  const pct = Math.round(value * 100);
  const fillColor = inverse
    ? pct >= 75 ? "bg-destructive"
      : pct >= 45 ? "bg-amber-500"
      : "bg-success"
    : pct >= 75 ? "bg-success"
      : pct >= 45 ? "bg-amber-500"
      : "bg-destructive";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-mono tabular-nums">{pct}%</span>
      </div>
      <div className="h-1 bg-surface-hover rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${fillColor}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
        />
      </div>
    </div>
  );
});

const Section = memo(function Section({ title, content }: { title: string; content: string }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-0.5 h-4 rounded-full bg-primary shrink-0" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          {title}
        </h3>
      </div>
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
    <motion.div
      id="decision-document"
      className="w-full space-y-8 relative"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Sticky section jump-nav */}
      <div className="sticky top-0 z-30 flex items-center gap-3 overflow-x-auto py-2 bg-background/90 backdrop-blur-md border-b border-border/40 text-xs font-mono text-muted-foreground hide-scrollbar">
        <span className="text-[10px] uppercase font-bold text-muted-foreground/60 shrink-0">Jump to:</span>
        <a href="#sec-summary" className="hover:text-primary transition-colors shrink-0">Summary</a>
        <span className="text-border">·</span>
        <a href="#sec-rec" className="hover:text-primary transition-colors shrink-0">Recommendation</a>
        <span className="text-border">·</span>
        <a href="#sec-visuals" className="hover:text-primary transition-colors shrink-0">Visuals</a>
        <span className="text-border">·</span>
        <a href="#sec-tradeoffs" className="hover:text-primary transition-colors shrink-0">Tradeoffs</a>
        <span className="text-border">·</span>
        <a href="#sec-alternatives" className="hover:text-primary transition-colors shrink-0">Alternatives</a>
      </div>

      {/* Header */}
      <div className="border-b border-border pb-5 space-y-1">
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <span className="uppercase tracking-widest">Decision Document</span>
          <span className="text-border">·</span>
          <span>v{doc.version}</span>
          <span className="text-border">·</span>
          <span suppressHydrationWarning>{new Date(doc.created_at).toLocaleDateString()}</span>
        </div>
        <h2 className="text-xl font-semibold text-foreground leading-snug mt-2">{doc.question}</h2>
      </div>

      {/* Executive Summary */}
      <div id="sec-summary">
        <Section title="Executive Summary" content={doc.executive_summary} />
      </div>

      {/* Memory Influence Transparency */}
      {doc.memory_context && (
        <MemoryUsed context={doc.memory_context} />
      )}

      {/* Recommendation */}
      <div id="sec-rec">
        <Section title="Recommendation" content={doc.recommendation_context} />
      </div>

      {/* Visuals Section */}
      <div id="sec-visuals">
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
      </div>

      {/* Tradeoffs */}
      <div id="sec-tradeoffs">
        <Section title="Tradeoffs" content={doc.tradeoffs} />
      </div>

      {/* Alternatives */}
      <div id="sec-alternatives">
        <Section title="Alternatives" content={doc.alternatives} />
      </div>
    </motion.div>
  );
}

export function AuxiliaryDocumentData({ doc, sessionId, onRefresh }: { doc: DecisionDocumentType, sessionId: string, onRefresh: (id: string) => void }) {
  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, x: 8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Confidence */}
      <div className="space-y-3 rounded-lg border border-border bg-surface p-4">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">
          Confidence Breakdown
        </h3>
        <ConfidenceBar label="Evidence Coverage"   value={doc.confidence.evidence_coverage} />
        <ConfidenceBar label="Source Quality"       value={doc.confidence.source_quality} />
        <ConfidenceBar label="Contradiction Risk"   value={doc.confidence.contradiction_risk} inverse />
        <ConfidenceBar label="Decision Confidence"  value={doc.confidence.decision_confidence} />
      </div>

      {/* Evidence Section */}
      {doc.evidence && doc.evidence.length > 0 && (
        <div className="space-y-4">
          <EvidenceCard evidence={doc.evidence} />
          <EvidenceConsensus consensus={doc.consensus} />
        </div>
      )}

      <RefreshEvidence question={doc.question} onRefresh={onRefresh} />

      {/* Footer */}
      <p className="text-xs text-muted-foreground font-mono border-t border-border/50 pt-3" suppressHydrationWarning>
        Generated {new Date(doc.created_at).toLocaleString()}
        {doc.evidence_generated_at && (
          <><br />Evidence refreshed {new Date(doc.evidence_generated_at).toLocaleString()}</>
        )}
      </p>
    </motion.div>
  );
}
