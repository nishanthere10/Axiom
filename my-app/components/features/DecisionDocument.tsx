"use client";

import { useEffect, useState } from "react";
import { getSessionDocument } from "@/lib/api";
import type { DecisionDocument } from "@/types";

interface Props {
  sessionId: string;
}

function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="text-foreground font-mono">{pct}%</span>
      </div>
      <div className="h-1 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

import ReactMarkdown from "react-markdown";

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        {title}
      </h3>
      <div className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}

import EvidenceCard from "./EvidenceCard";
import EvidenceConsensus from "./EvidenceConsensus";
import RefreshEvidence from "./RefreshEvidence";

export default function DecisionDocument({ sessionId }: Props) {
  const [doc, setDoc] = useState<DecisionDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDoc = async (id: string) => {
    try {
      const data = await getSessionDocument(id);
      setDoc(data.document);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load document.");
    }
  };

  useEffect(() => {
    fetchDoc(sessionId);
  }, [sessionId]);

  const handleRefresh = (newSessionId: string) => {
    fetchDoc(newSessionId);
  };

  if (error) {
    return (
      <p className="text-sm text-destructive text-center" role="alert">
        {error}
      </p>
    );
  }

  if (!doc) {
    return (
      <p className="text-sm text-muted-foreground text-center" aria-live="polite">
        Loading document…
      </p>
    );
  }

  return (
    <div id="decision-document" className="w-full max-w-2xl mx-auto space-y-8">
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

      {/* Recommendation */}
      <Section title="Recommendation" content={doc.recommendation_context} />

      {/* Evidence Section */}
      {doc.evidence && doc.evidence.length > 0 && (
        <>
          <EvidenceCard evidence={doc.evidence} />
          <EvidenceConsensus consensus={doc.consensus} />
        </>
      )}

      {/* Tradeoffs */}
      <Section title="Tradeoffs" content={doc.tradeoffs} />

      {/* Alternatives */}
      <Section title="Alternatives" content={doc.alternatives} />

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

      <RefreshEvidence question={doc.question} onRefresh={handleRefresh} />

      {/* Footer */}
      <p className="text-xs text-muted-foreground text-right">
        Generated at {new Date(doc.created_at).toLocaleString()}
        {doc.evidence_generated_at && ` (Evidence retrieved at ${new Date(doc.evidence_generated_at).toLocaleString()})`}
      </p>
    </div>
  );
}
