"use client";

import { useEffect, useRef, useState } from "react";
import { getJobStatus } from "@/lib/api";
import { PollingState } from "@/types";

const STEP_LABELS: Record<string, string> = {
  "": "Initializing…",
  starting: "Starting…",
  decompose_question: "Decomposing question…",
  generate_decision: "Generating decision…",
  build_confidence: "Evaluating confidence…",
  format_document: "Formatting document…",
  done: "Complete",
  error: "An error occurred.",
};

interface Props {
  jobId: string;
  onComplete: () => void;
  onFailed: (error: string) => void;
}

export default function ResearchProgress({ jobId, onComplete, onFailed }: Props) {
  const [status, setStatus] = useState<PollingState>("queued");
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status as PollingState);
        setProgress(data.progress);
        setStep(data.step);

        if (data.status === "completed") {
          clearInterval(intervalRef.current!);
          onComplete();
        } else if (data.status === "failed") {
          clearInterval(intervalRef.current!);
          onFailed("The research job failed. Please try again.");
        }
      } catch {
        // Network errors — keep polling
      }
    }, 2000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId, onComplete, onFailed]);

  const stepLabel = STEP_LABELS[step] ?? step;

  return (
    <div
      id="research-progress"
      className="w-full max-w-2xl mx-auto space-y-6"
      role="status"
      aria-live="polite"
    >
      <div className="text-center space-y-1">
        <p className="text-sm font-medium text-foreground">
          {status === "queued" ? "Queued — waiting for worker…" : stepLabel}
        </p>
        <p className="text-xs text-muted-foreground uppercase tracking-widest">
          {status}
        </p>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-700 ease-in-out rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps indicator */}
      <div className="grid grid-cols-4 gap-1 text-center">
        {["decompose_question", "generate_decision", "build_confidence", "format_document"].map(
          (node, idx) => {
            const nodeProgress = [25, 60, 85, 100][idx];
            const isDone = progress >= nodeProgress;
            const isActive = step === node;

            return (
              <div key={node} className="space-y-1">
                <div
                  className={`h-1 w-full rounded-full transition-colors duration-500 ${
                    isDone ? "bg-primary" : isActive ? "bg-primary/40" : "bg-secondary"
                  }`}
                />
                <p
                  className={`text-[10px] leading-tight ${
                    isDone || isActive ? "text-foreground" : "text-muted-foreground"
                  }`}
                >
                  {["Decompose", "Generate", "Evaluate", "Format"][idx]}
                </p>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}
