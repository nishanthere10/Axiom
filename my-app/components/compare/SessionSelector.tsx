"use client";

import { useState, useEffect } from "react";
import { getRecentSessions } from "@/lib/compare";

interface Props {
  onCompare: (sessionA: string, sessionB: string) => void;
  disabled: boolean;
}

export default function SessionSelector({ onCompare, disabled }: Props) {
  const [sessionA, setSessionA] = useState("");
  const [sessionB, setSessionB] = useState("");
  const [recentSessions, setRecentSessions] = useState<{ id: string; question: string; created_at: string }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const sessions = await getRecentSessions();
        setRecentSessions(sessions);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (sessionA && sessionB) {
      onCompare(sessionA, sessionB);
    }
  };

  // Filter out Session A from the options of Session B
  const sessionBOptions = recentSessions.filter(s => s.id !== sessionA);

  return (
    <div className="w-full max-w-2xl mx-auto space-y-8">
      <div className="space-y-2 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-foreground">Compare Decisions</h2>
        <p className="text-muted-foreground text-sm">
          Select two historical decisions to analyze how and why your architecture evolved.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Session A (Baseline)
            </label>
            {loading ? (
              <p className="text-sm text-muted-foreground py-3">Loading recent sessions...</p>
            ) : (
              <select
                required
                value={sessionA}
                onChange={(e) => {
                  setSessionA(e.target.value);
                  setSessionB(""); // reset B when A changes
                }}
                className="w-full bg-transparent border-b-2 border-border py-3 px-0 focus:outline-none focus:border-primary transition-colors text-foreground text-sm cursor-pointer"
                disabled={disabled}
              >
                <option value="" disabled className="bg-background">Select a past decision</option>
                {recentSessions.map(s => (
                  <option key={s.id} value={s.id} className="bg-background">
                    {new Date(s.created_at).toLocaleDateString()} — {s.question}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Session B (Evolution)
            </label>
            <select
              required
              value={sessionB}
              onChange={(e) => setSessionB(e.target.value)}
              className="w-full bg-transparent border-b-2 border-border py-3 px-0 focus:outline-none focus:border-primary transition-colors text-foreground text-sm cursor-pointer"
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
          </div>
        </div>

        <button
          type="submit"
          disabled={disabled || !sessionA || !sessionB || sessionA === sessionB}
          className="w-full bg-foreground text-background py-4 uppercase tracking-widest font-semibold text-sm hover:bg-foreground/90 transition-colors disabled:opacity-50"
        >
          Compare Decisions
        </button>
      </form>
    </div>
  );
}
