"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { getRecentSessions } from "@/lib/compare";

interface ResearchSessionItem {
  id: string;
  question: string;
  created_at: string;
}

import { useWorkspace } from "../layout";

export default function SavedResearchPage() {
  const { getToken } = useAuth();
  const [sessions, setSessions] = useState<ResearchSessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { hideRightPanel } = useWorkspace();

  useEffect(() => {
    hideRightPanel();
  }, [hideRightPanel]);

  useEffect(() => {
    async function loadSessions() {
      try {
        const token = await getToken() ?? "";
        const data = await getRecentSessions(token);
        setSessions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load saved research documents.");
      } finally {
        setLoading(false);
      }
    }

    loadSessions();
  }, []);

  return (
    <>
      <div className="w-full space-y-8 animate-in fade-in duration-300">
        <div className="border-b border-border pb-4">
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/75 bg-clip-text">
            Saved Research
          </h1>
          <p className="text-sm text-muted-foreground mt-2">
            Browse and read your completed AI-powered technical research documents.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-24">
            <div className="flex flex-col items-center space-y-4">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="text-muted-foreground text-xs tracking-widest uppercase animate-pulse">
                Loading research...
              </p>
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-12 space-y-4">
            <p className="text-destructive text-sm">{error}</p>
            <button 
              onClick={() => {
                setLoading(true);
                setError(null);
                getToken().then(t => getRecentSessions(t ?? "")).then(setSessions).catch(e => setError(e.message)).finally(() => setLoading(false));
              }}
              className="text-xs text-primary hover:underline"
            >
              Retry loading
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-border rounded-xl bg-card/50">
            <p className="text-muted-foreground text-sm">
              No saved research documents found.
            </p>
            <div className="mt-6">
              <Link
                href="/"
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground shadow hover:bg-primary/95 h-9 px-4 py-2"
              >
                Start New Research
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {sessions.map((session) => (
              <Link
                key={session.id}
                href={`/research?session_id=${session.id}`}
                className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:border-primary/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <div className="space-y-4">
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono font-medium tracking-wider text-primary uppercase bg-primary/10 px-2 py-0.5 rounded-full">
                      Research Doc
                    </span>
                    <h3 className="font-semibold text-base line-clamp-3 group-hover:text-primary transition-colors leading-snug">
                      {session.question}
                    </h3>
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono bg-muted/40 px-2 py-0.5 rounded text-[10px]">
                    ID: {session.id.substring(0, 8)}
                  </span>
                  <span>{new Date(session.created_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                  })}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
