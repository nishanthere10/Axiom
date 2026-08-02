"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { getRecentSessions } from "@/lib/compare";
import { ArrowRight, ChevronDown } from "lucide-react";

interface Props {
  onCompare: (sessionA: string, sessionB: string) => void;
  disabled: boolean;
}

export default function SessionSelector({ onCompare, disabled }: Props) {
  const { getToken } = useAuth();
  const params = useParams();
  const workspaceId = params?.id as string | undefined;
  const [sessionA, setSessionA] = useState("");
  const [sessionB, setSessionB] = useState("");
  const [recentSessions, setRecentSessions] = useState<{ id: string; question: string; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken() ?? "";
        const sessions = await getRecentSessions(token, workspaceId);
        setRecentSessions(sessions);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (sessionA && sessionB) {
      onCompare(sessionA, sessionB);
    }
  };

  // Filter out Session A from the options of Session B
  const sessionBOptions = recentSessions.filter(s => s.id !== sessionA);

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="mb-10 text-center space-y-3">
        <h2 className="text-2xl md:text-3xl font-medium tracking-tight text-foreground">Compare Decisions</h2>
        <p className="text-sm text-muted-foreground">
          Select two historical decisions to analyze how and why your architecture evolved.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-5">
          {/* Baseline Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground ml-1">
              Session A (Baseline)
            </label>
            <div className="relative group rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-border/80 hover:bg-surface/80 focus-within:!bg-surface focus-within:shadow-md focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all duration-300">
              {loading ? (
                <div className="w-full p-4 text-sm text-muted-foreground">Loading recent sessions...</div>
              ) : (
                <>
                  <select
                    required
                    value={sessionA}
                    onChange={(e) => {
                      setSessionA(e.target.value);
                      setSessionB(""); // reset B when A changes
                    }}
                    className="w-full bg-transparent p-4 focus:outline-none transition-colors text-foreground text-sm cursor-pointer appearance-none"
                    disabled={disabled}
                  >
                    <option value="" disabled className="bg-background">Select a past decision</option>
                    {recentSessions.map(s => (
                      <option key={s.id} value={s.id} className="bg-background">
                        {new Date(s.created_at).toLocaleDateString()} — {s.question}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground/60 group-hover:text-muted-foreground transition-colors">
                    <ChevronDown className="w-4 h-4" />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Evolution Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground ml-1">
              Session B (Evolution)
            </label>
            <div className="relative group rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-border/80 hover:bg-surface/80 focus-within:!bg-surface focus-within:shadow-md focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/50 transition-all duration-300">
              <select
                required
                value={sessionB}
                onChange={(e) => setSessionB(e.target.value)}
                className="w-full bg-transparent p-4 focus:outline-none transition-colors text-foreground text-sm cursor-pointer appearance-none"
                disabled={disabled || !sessionA}
              >
                <option value="" disabled className="bg-background">
                  {sessionA ? "Select a second decision to compare" : "Select Session A first"}
                </option>
                {sessionBOptions.map(s => (
                  <option key={s.id} value={s.id} className="bg-background">
                    {new Date(s.created_at).toLocaleDateString()} — {s.question}
                  </option>
                ))}
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground/60 group-hover:text-muted-foreground transition-colors">
                <ChevronDown className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={disabled || !sessionA || !sessionB || sessionA === sessionB}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 focus:ring-2 focus:ring-primary/50 disabled:opacity-50 transition-all duration-200 shadow-sm"
        >
          Compare Decisions
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
