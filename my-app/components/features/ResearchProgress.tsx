"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { API_BASE_URL } from "@/lib/api";
import ResearchProgressUI from "./ResearchProgressUI";

interface ProgressEvent {
  status: "running" | "completed" | "failed" | "connected" | "timeout";
  progress?: number;
  step?: string;
  node?: string;
  session_id?: string;
  error?: string;
  meta?: {
    memories_found?: number;
    memory_summaries?: string[];
    github_chunks?: number;
  };
}

interface ResearchProgressProps {
  jobId: string;
  workspaceId: string;
  onComplete: (sessionId?: string) => void;
  onFailed: (error: string) => void;
}

export default function ResearchProgress({
  jobId,
  workspaceId,
  onComplete,
  onFailed,
}: ResearchProgressProps) {
  const { getToken } = useAuth();
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("Starting…");
  const [completedNodes, setCompletedNodes] = useState<Array<{ node: string; step: string; meta?: ProgressEvent["meta"] }>>([]);
  const esRef = useRef<EventSource | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startPollingFallback = useCallback(async () => {
    if (pollingRef.current) return;
    if (!workspaceId || workspaceId === "undefined") return;
    
    pollingRef.current = setInterval(async () => {
      try {
        const token = await getToken();
        const res = await fetch(
          `${API_BASE_URL}/workspaces/${workspaceId}/research/jobs/${jobId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!res.ok) return;
        const data = await res.json();
        setProgress(data.progress ?? 0);
        setStep(data.step ?? "");
        if (data.status === "completed") {
          clearInterval(pollingRef.current!);
          onComplete();
        }
        if (data.status === "failed") {
          clearInterval(pollingRef.current!);
          onFailed("Research failed. Please try again.");
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 2000);
  }, [jobId, workspaceId, getToken, onComplete, onFailed]);

  useEffect(() => {
    if (!jobId || !workspaceId || workspaceId === "undefined") return;
    let cancelled = false;

    async function startSSE() {
      try {
        // Step 1: get auth ticket
        const token = await getToken();
        if (!token || cancelled) return;

        const ticketRes = await fetch(
          `${API_BASE_URL}/workspaces/${workspaceId}/research/jobs/${jobId}/stream-ticket`,
          { method: "POST", headers: { Authorization: `Bearer ${token}` } }
        );
        if (!ticketRes.ok) {
          startPollingFallback();
          return;
        }
        const { ticket } = await ticketRes.json();
        if (cancelled) return;

        // Step 2: open SSE with ticket
        const sseUrl = `${API_BASE_URL}/workspaces/${workspaceId}/research/jobs/${jobId}/stream?ticket=${ticket}`;
        const es = new EventSource(sseUrl);
        esRef.current = es;

        es.onmessage = (e) => {
          const data: ProgressEvent = JSON.parse(e.data);

          if (data.progress !== undefined) setProgress(data.progress);
          if (data.step) setStep(data.step);

          if (data.node && data.step) {
            setCompletedNodes((prev) => {
              const already = prev.find((n) => n.node === data.node);
              if (already) return prev;
              return [...prev, { node: data.node!, step: data.step!, meta: data.meta }];
            });
          }

          if (data.status === "completed") {
            es.close();
            onComplete(data.session_id);
          }
          if (data.status === "failed") {
            es.close();
            onFailed(data.error ?? "Research failed.");
          }
        };

        es.onerror = () => {
          es.close();
          if (!cancelled) startPollingFallback();
        };

      } catch {
        if (!cancelled) startPollingFallback();
      }
    }

    startSSE();

    return () => {
      cancelled = true;
      esRef.current?.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [jobId, workspaceId, getToken, onComplete, onFailed, startPollingFallback]);

  return (
    <ResearchProgressUI
      progress={progress}
      currentStep={step}
      completedNodes={completedNodes}
    />
  );
}
