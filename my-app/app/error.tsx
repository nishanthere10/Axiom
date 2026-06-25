"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service like Sentry here if available
    console.error("Caught in app/error.tsx:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-6">
      <div className="w-full max-w-md p-8 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-md shadow-xl text-center space-y-6">
        <div className="w-16 h-16 bg-destructive/10 border border-destructive/20 text-destructive rounded-full flex items-center justify-center mx-auto mb-2 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
          <AlertTriangle className="w-8 h-8" />
        </div>
        
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground mb-2">Something went wrong!</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            We encountered an unexpected error while rendering this page. The issue has been logged.
          </p>
          <div className="mt-4 p-3 bg-surface/80 rounded-lg border border-border/40 text-left overflow-hidden">
            <code className="text-[10px] text-destructive/80 break-words font-mono block">
              {error.message || "Unknown Application Error"}
            </code>
          </div>
        </div>

        <div className="flex flex-col gap-3 pt-4">
          <button
            onClick={() => reset()}
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors h-11 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
          >
            <RefreshCw className="w-4 h-4" /> Try again
          </button>
          
          <Link
            href="/"
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors h-11 border border-border/60 bg-surface/50 text-foreground hover:bg-surface hover:border-border/80"
          >
            <Home className="w-4 h-4" /> Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
