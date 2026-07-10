"use client";

import { cn } from "@/lib/utils";
import { CheckCircle2, Loader2 } from "lucide-react";

const ALL_STEPS = [
  { node: "decompose_question",         label: "Understanding your question" },
  { node: "retrieve_memory",            label: "Checking knowledge archive" },
  { node: "retrieve_github_context",    label: "Reading your codebase" },
  { node: "analyze_memory",             label: "Analyzing past decisions" },
  { node: "generate_queries",           label: "Building research queries" },
  { node: "collect_and_score_evidence", label: "Searching and scoring evidence" },
  { node: "generate_decision",          label: "Generating recommendation" },
  { node: "build_confidence",           label: "Scoring confidence" },
  { node: "generate_visual_spec",       label: "Creating diagrams" },
  { node: "format_document",            label: "Assembling report" },
];

interface CompletedNode {
  node: string;
  step: string;
  meta?: {
    memories_found?: number;
    memory_summaries?: string[];
    github_chunks?: number;
  };
}

interface Props {
  progress: number;
  currentStep: string;
  completedNodes: CompletedNode[];
}

export default function ResearchProgressUI({ progress, currentStep, completedNodes }: Props) {
  const completedSet = new Set(completedNodes.map((n) => n.node));

  return (
    <div className="w-full max-w-lg mx-auto space-y-6">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{currentStep}</span>
          <span className="font-mono">{progress}%</span>
        </div>
        <div className="h-1.5 w-full bg-surface rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-[width] duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="space-y-1">
        {ALL_STEPS.map((step, idx) => {
          const completed = completedSet.has(step.node);
          const completedData = completedNodes.find((n) => n.node === step.node);
          // Determine if this is the "current" step (first not-yet-completed step after last done)
          const lastCompletedIdx = Math.max(
            ...completedNodes.map((n) => ALL_STEPS.findIndex((s) => s.node === n.node)),
            -1
          );
          const isCurrent = !completed && idx === lastCompletedIdx + 1;
          const isPending = !completed && !isCurrent;

          return (
            <div key={step.node} className="space-y-0.5">
              <div className={cn(
                "flex items-center gap-2.5 py-1 text-sm transition-colors",
                completed && "text-foreground",
                isCurrent && "text-primary font-medium",
                isPending && "text-muted-foreground/50"
              )}>
                <span className="w-4 h-4 shrink-0 flex items-center justify-center">
                  {completed ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-border" />
                  )}
                </span>
                <span>{step.label}</span>

                {/* Inline memory count badge */}
                {completed && completedData?.meta?.memories_found !== undefined && (
                  <span className="ml-auto text-xs text-muted-foreground font-mono">
                    {completedData.meta.memories_found} memories
                  </span>
                )}
                {completed && completedData?.meta?.github_chunks !== undefined && (
                  <span className="ml-auto text-xs text-muted-foreground font-mono">
                    {completedData.meta.github_chunks} docs
                  </span>
                )}
              </div>

              {/* Expand memory summaries inline */}
              {completed && completedData?.meta?.memory_summaries && completedData.meta.memory_summaries.length > 0 && (
                <div className="pl-7 space-y-0.5">
                  {completedData.meta.memory_summaries.map((s, i) => (
                    <p key={i} className="text-xs text-muted-foreground line-clamp-1">· {s}</p>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
