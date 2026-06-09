"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import QuestionInput from "@/components/features/QuestionInput";
import ResearchProgress from "@/components/features/ResearchProgress";
import { getSessionDocument } from "@/lib/api";
import ResizableLayout from "@/components/ui/ResizableLayout";
import type { DecisionDocument as DecisionDocumentType, PollingState, ResearchResponse } from "@/types";
import DecisionDocument, { AuxiliaryDocumentData } from "@/components/features/DecisionDocument";

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
        <>
          {pageState === "done" && sessionId && doc && (
            <AuxiliaryDocumentData doc={doc} sessionId={sessionId} onRefresh={handleRefreshEvidence} />
          )}
          {pageState !== "done" && (
            <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-2 opacity-50">
              <p className="text-sm text-muted-foreground font-medium">Awaiting Research</p>
              <p className="text-xs text-muted-foreground max-w-[200px]">
                Evidence and confidence scores will appear here.
              </p>
            </div>
          )}
        </>
      }
    >
      {pageState === "idle" && (
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
           <QuestionInput onSubmitted={handleSubmitted} />
        </div>
      )}

      {pageState === "polling" && jobId && (
        <div className="w-full max-w-2xl mx-auto space-y-6 pt-16">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-semibold text-foreground tracking-tight">
              Generating Decision…
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              This usually takes under 20 seconds.
            </p>
          </div>
          <ResearchProgress
            jobId={jobId}
            onComplete={handleComplete}
            onFailed={handleFailed}
          />
        </div>
      )}

      {pageState === "done" && sessionId && doc && (
        <div className="w-full space-y-8 animate-in fade-in duration-300">
          <DecisionDocument doc={doc} sessionId={sessionId} setDoc={setDoc} />
          <div className="text-center pt-8 border-t border-border/50">
            <button
              id="new-research-btn"
              onClick={handleReset}
              className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors"
            >
              Start new research
            </button>
          </div>
        </div>
      )}

      {pageState === "done" && sessionId && !doc && (
        <p className="text-sm text-muted-foreground text-center pt-16" aria-live="polite">
          Loading document…
        </p>
      )}

      {pageState === "failed" && (
        <div className="w-full max-w-2xl mx-auto text-center space-y-4 pt-16">
          <p className="text-sm text-destructive">{errorMessage}</p>
          <button
            id="retry-research-btn"
            onClick={handleReset}
            className="text-sm text-muted-foreground hover:text-foreground underline underline-offset-4 transition-colors"
          >
            Try again
          </button>
        </div>
      )}
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

