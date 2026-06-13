"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { AnimatePresence, motion } from "framer-motion";
import QuestionInput from "@/components/features/QuestionInput";
import ResearchProgress from "@/components/features/ResearchProgress";
import { getSessionDocument } from "@/lib/api";
import ResizableLayout from "@/components/ui/ResizableLayout";
import type { DecisionDocument as DecisionDocumentType, PollingState, ResearchResponse } from "@/types";
import DecisionDocument, { AuxiliaryDocumentData } from "@/components/features/DecisionDocument";
import ExportButton from "@/components/export/ExportButton";

type PageState = "idle" | "polling" | "done" | "failed";

function ResearchPageInner() {
  const { getToken } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [pageState, setPageState] = useState<PageState>("idle");
  const [pollingState, setPollingState] = useState<PollingState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [doc, setDoc] = useState<DecisionDocumentType | null>(null);

  useEffect(() => {
    const urlSessionId = searchParams.get("session_id");
    if (urlSessionId && pageState === "idle") {
      setSessionId(urlSessionId);
      setPageState("done");
    }
  }, [searchParams, pageState]);

  const fetchDoc = useCallback(async (id: string) => {
    try {
      const token = await getToken() ?? "";
      const data = await getSessionDocument(id, token);
      setDoc(data.document);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load document.");
      setPageState("failed");
    }
  }, []);

  useEffect(() => {
    if (pageState === "done" && sessionId) {
      fetchDoc(sessionId);
    }
  }, [pageState, sessionId, fetchDoc]);

  function handleSubmitted(response: ResearchResponse) {
    setJobId(response.job_id);
    setSessionId(response.session_id);
    setPollingState("queued");
    setPageState("polling");
  }

  const handleComplete = useCallback(() => {
    setPollingState("completed");
    setPageState("done");
    if (sessionId) {
      router.push(`/research?session_id=${sessionId}`);
    }
  }, [router, sessionId]);

  const handleFailed = useCallback((error: string) => {
    setPollingState("failed");
    setPageState("failed");
    setErrorMessage(error);
  }, []);

  function handleReset() {
    setPageState("idle");
    setPollingState("idle");
    setJobId(null);
    setSessionId(null);
    setDoc(null);
    setErrorMessage(null);
    router.push("/research");
  }

  const handleRefreshEvidence = (newSessionId: string) => {
    fetchDoc(newSessionId);
  };

  return (
    <ResizableLayout
      rightPanelTitle="Evidence & Confidence"
      rightPanelContent={
        <AnimatePresence mode="wait">
          {pageState === "done" && sessionId && doc ? (
            <motion.div
              key="aux"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <AuxiliaryDocumentData doc={doc} sessionId={sessionId} onRefresh={handleRefreshEvidence} />
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center justify-center h-[50vh] text-center space-y-2 opacity-50"
            >
              <p className="text-sm text-muted-foreground font-medium">Awaiting Research</p>
              <p className="text-xs text-muted-foreground max-w-[200px]">
                Evidence and confidence scores will appear here.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      }
    >
      <AnimatePresence mode="wait">
        {pageState === "idle" && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            className="flex flex-col items-center justify-center min-h-[60vh]"
          >
            <QuestionInput onSubmitted={handleSubmitted} />
          </motion.div>
        )}

        {pageState === "polling" && jobId && (
          <motion.div
            key="polling"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
            className="w-full max-w-2xl mx-auto space-y-6 pt-16"
          >
            <div className="text-center mb-8">
              <h1 className="text-2xl font-semibold text-foreground tracking-tight">
                Generating Decision…
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                This usually takes under 20 seconds.
              </p>
            </div>
            <ResearchProgress jobId={jobId} onComplete={handleComplete} onFailed={handleFailed} />
          </motion.div>
        )}

        {pageState === "done" && sessionId && doc && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="w-full space-y-8"
          >
            <div className="flex justify-end no-print mb-4">
              <ExportButton />
            </div>
            <DecisionDocument doc={doc} sessionId={sessionId} setDoc={setDoc} />
            <div className="text-center pt-8 border-t border-border/50 no-print">
              <button
                id="new-research-btn"
                onClick={handleReset}
                className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors font-mono"
              >
                Start new research
              </button>
            </div>
          </motion.div>
        )}

        {pageState === "done" && sessionId && !doc && (
          <motion.p
            key="loading-doc"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm text-muted-foreground text-center pt-16"
            aria-live="polite"
          >
            Loading document…
          </motion.p>
        )}

        {pageState === "failed" && (
          <motion.div
            key="failed"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="w-full max-w-2xl mx-auto text-center space-y-4 pt-16"
          >
            <div className="p-4 rounded-lg border border-destructive/30 bg-destructive/10">
              <p className="text-sm text-destructive-foreground">{errorMessage}</p>
            </div>
            <button
              id="retry-research-btn"
              onClick={handleReset}
              className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors font-mono"
            >
              Try again
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </ResizableLayout>
  );
}

export default function ResearchPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-background flex items-center justify-center">
          <p className="text-muted-foreground text-sm">Loading…</p>
        </main>
      }
    >
      <ResearchPageInner />
    </Suspense>
  );
}

