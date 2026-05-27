"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import QuestionInput from "@/components/features/QuestionInput";
import ResearchProgress from "@/components/features/ResearchProgress";
import DecisionDocument from "@/components/features/DecisionDocument";
import { ResearchResponse, PollingState } from "@/types";

type PageState = "idle" | "polling" | "done" | "failed";

function ResearchPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [pageState, setPageState] = useState<PageState>("idle");
  const [pollingState, setPollingState] = useState<PollingState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Restore from URL params on refresh
  useEffect(() => {
    const urlSessionId = searchParams.get("session_id");
    if (urlSessionId && pageState === "idle") {
      setSessionId(urlSessionId);
      setPageState("done");
    }
  }, [searchParams, pageState]);

  function handleSubmitted(response: ResearchResponse) {
    setJobId(response.job_id);
    setSessionId(response.session_id);
    setPollingState("queued");
    setPageState("polling");
    // We do NOT push to the URL here. We wait until polling is complete.
  }

  const handleComplete = useCallback(() => {
    setPollingState("completed");
    setPageState("done");
    // Now that the document is generated, persist it in the URL
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
    setErrorMessage(null);
    router.push("/research");
  }

  return (
    <main className="min-h-screen bg-background flex flex-col items-center justify-center px-4 py-16">
      {pageState === "idle" && <QuestionInput onSubmitted={handleSubmitted} />}

      {pageState === "polling" && jobId && (
        <div className="w-full max-w-2xl mx-auto space-y-6">
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

      {pageState === "done" && sessionId && (
        <div className="w-full space-y-8">
          <DecisionDocument sessionId={sessionId} />
          <div className="text-center">
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

      {pageState === "failed" && (
        <div className="w-full max-w-2xl mx-auto text-center space-y-4">
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
    </main>
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

