"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { getJobStatus } from "@/lib/api";
import { PollingState } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle } from "lucide-react";

const PIPELINE_STEPS = [
  { key: "decompose_question", label: "Decompose",  threshold: 25 },
  { key: "generate_decision",  label: "Generate",   threshold: 60 },
  { key: "build_confidence",   label: "Evaluate",   threshold: 85 },
  { key: "format_document",    label: "Format",     threshold: 100 },
];

const STEP_LABELS: Record<string, string> = {
  "":                   "Initializing…",
  starting:             "Starting…",
  decompose_question:   "Decomposing question…",
  generate_decision:    "Generating decision…",
  build_confidence:     "Evaluating confidence…",
  format_document:      "Formatting document…",
  done:                 "Complete",
  error:                "An error occurred.",
};

interface Props {
  jobId: string;
  onComplete: () => void;
  onFailed: (error: string) => void;
}

export default function ResearchProgress({ jobId, onComplete, onFailed }: Props) {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<PollingState>("queued");
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("");
  const [logLines, setLogLines] = useState<string[]>(["[ system ] Job queued. Waiting for worker…"]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    intervalRef.current = setInterval(async () => {
      try {
        const token = (await getToken()) ?? "";
        const data = await getJobStatus(jobId, token);
        setStatus(data.status as PollingState);
        setProgress(data.progress);
        setStep(data.step);

        const label = STEP_LABELS[data.step] ?? data.step;
        if (label) {
          setLogLines(prev => {
            const last = prev[prev.length - 1];
            const next = `[ ${data.step || "init"} ] ${label}`;
            return last === next ? prev : [...prev, next];
          });
        }

        if (data.status === "completed") {
          clearInterval(intervalRef.current!);
          setLogLines(prev => [...prev, "[ done ] Pipeline complete. Loading document…"]);
          onComplete();
        } else if (data.status === "failed") {
          clearInterval(intervalRef.current!);
          setLogLines(prev => [...prev, "[ error ] Job failed. Please retry."]);
          onFailed("The research job failed. Please try again.");
        }
      } catch {
        // Network errors — keep polling
      }
    }, 2000);

    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [jobId, onComplete, onFailed]);

  // Auto-scroll log to bottom
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logLines]);

  const stepLabel = STEP_LABELS[step] ?? step;

  return (
    <div
      id="research-progress"
      className="w-full max-w-2xl mx-auto space-y-6"
      role="status"
      aria-live="polite"
    >
      {/* Status line */}
      <div className="flex items-center justify-between">
        <AnimatePresence mode="wait">
          <motion.p
            key={stepLabel}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
            className="text-sm font-medium text-foreground"
          >
            {status === "queued" ? "Queued — waiting for worker…" : stepLabel}
          </motion.p>
        </AnimatePresence>
        <span className="text-xs font-mono text-muted-foreground tabular-nums">
          {progress}%
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1 bg-surface-hover rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-primary rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>

      {/* Pipeline step indicators */}
      <div className="grid grid-cols-4 gap-2">
        {PIPELINE_STEPS.map(({ key, label, threshold }) => {
          const isDone   = progress >= threshold;
          const isActive = step === key;
          return (
            <div key={key} className="space-y-1.5 text-center">
              <div
                className={`h-px w-full rounded-full transition-colors duration-500 ${
                  isDone ? "bg-primary" : isActive ? "bg-primary/40" : "bg-surface-hover"
                }`}
              />
              <span className={`flex items-center justify-center text-[10px] font-mono transition-colors duration-300 h-4 ${
                isDone ? "text-primary" : isActive ? "text-foreground" : "text-muted-foreground"
              }`}>
                {isDone && !isActive
                  ? <CheckCircle className="w-3 h-3" />
                  : label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Monospace log terminal */}
      <div className="rounded-lg border border-border bg-surface p-4 h-36 overflow-y-auto font-mono text-xs space-y-1">
        {logLines.map((line, i) => {
          const isLast = i === logLines.length - 1;
          const isRunning = status !== "completed" && status !== "failed";
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              className="flex items-center gap-1.5 leading-relaxed"
            >
              <span className="text-muted-foreground">{line}</span>
              {isLast && isRunning && (
                <span className="inline-block w-1.5 h-3.5 bg-primary/70 animate-pulse rounded-sm shrink-0" />
              )}
            </motion.div>
          );
        })}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
