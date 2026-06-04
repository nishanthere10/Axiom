"use client";

import { useState } from "react";
import { Brain, ChevronDown, ChevronUp, AlertTriangle, Lightbulb, History, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface PreferenceInsight {
  value: string;
  reason: string;
}

interface MemoryContext {
  preferences: PreferenceInsight[];
  historical_patterns: string[];
  related_decisions: string[];
  consistency_warnings: string[];
}

function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "warning" | "info" | "success" }) {
  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
      variant === "default" && "bg-primary/10 text-primary",
      variant === "warning" && "bg-amber-500/10 text-amber-400",
      variant === "info" && "bg-blue-500/10 text-blue-400",
      variant === "success" && "bg-emerald-500/10 text-emerald-400",
    )}>
      {children}
    </span>
  );
}

export default function MemoryUsed({ context }: { context: MemoryContext }) {
  const [expanded, setExpanded] = useState(true);

  if (!context) return null;

  const hasWarnings = context.consistency_warnings?.length > 0;
  const hasPreferences = context.preferences?.length > 0;
  const hasPatterns = context.historical_patterns?.length > 0;
  const hasRelated = context.related_decisions?.length > 0;
  const hasAny = hasWarnings || hasPreferences || hasPatterns || hasRelated;

  if (!hasAny) return null;

  const totalInsights =
    (context.preferences?.length ?? 0) +
    (context.historical_patterns?.length ?? 0) +
    (context.related_decisions?.length ?? 0) +
    (context.consistency_warnings?.length ?? 0);

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      hasWarnings
        ? "border-amber-500/30 bg-amber-500/5"
        : "border-primary/20 bg-primary/5"
    )}>
      {/* Header — always visible, click to toggle */}
      <button
        onClick={() => setExpanded(prev => !prev)}
        className="w-full flex items-center justify-between px-5 py-4 text-left group"
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "flex items-center justify-center w-8 h-8 rounded-lg",
            hasWarnings ? "bg-amber-500/15 text-amber-400" : "bg-primary/15 text-primary"
          )}>
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Memory Influence Detected</p>
            <p className="text-xs text-muted-foreground">
              {totalInsights} insight{totalInsights !== 1 ? "s" : ""} from your past decisions shaped this recommendation
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasWarnings && <Badge variant="warning"><AlertTriangle className="w-3 h-3" />Warning</Badge>}
          {hasPreferences && <Badge variant="info">{context.preferences.length} Preference{context.preferences.length !== 1 ? "s" : ""}</Badge>}
          <span className="text-muted-foreground group-hover:text-foreground transition-colors">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </span>
        </div>
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-border/30 pt-4">

          {/* Consistency Warnings — shown first, most urgent */}
          {hasWarnings && (
            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5" />
                <p className="text-xs font-semibold uppercase tracking-widest">Consistency Warning</p>
              </div>
              <ul className="space-y-1.5">
                {context.consistency_warnings.map((warn, i) => (
                  <li key={i} className="text-sm text-amber-200/80 flex gap-2">
                    <span className="mt-1 shrink-0 w-1.5 h-1.5 rounded-full bg-amber-400" />
                    {warn}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Detected Preferences */}
          {hasPreferences && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-blue-400">
                <Sparkles className="w-3.5 h-3.5" />
                <p className="text-xs font-semibold uppercase tracking-widest">Your Preferences Applied</p>
              </div>
              <ul className="space-y-2">
                {context.preferences.map((pref, i) => (
                  <li key={i} className="flex gap-3 text-sm">
                    <span className="mt-1 shrink-0 w-1.5 h-1.5 rounded-full bg-blue-400" />
                    <span>
                      <span className="font-semibold text-foreground">{pref.value}</span>
                      <span className="text-muted-foreground"> — {pref.reason}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Historical Patterns */}
          {hasPatterns && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-emerald-400">
                <Lightbulb className="w-3.5 h-3.5" />
                <p className="text-xs font-semibold uppercase tracking-widest">Historical Patterns</p>
              </div>
              <ul className="space-y-1.5">
                {context.historical_patterns.map((pat, i) => (
                  <li key={i} className="text-sm text-foreground/70 flex gap-2">
                    <span className="mt-1 shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    {pat}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Related Past Decisions */}
          {hasRelated && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-purple-400">
                <History className="w-3.5 h-3.5" />
                <p className="text-xs font-semibold uppercase tracking-widest">Related Past Decisions</p>
              </div>
              <ul className="space-y-1.5">
                {context.related_decisions.map((dec, i) => (
                  <li key={i} className="text-sm text-foreground/70 flex gap-2">
                    <span className="mt-1 shrink-0 w-1.5 h-1.5 rounded-full bg-purple-400" />
                    {dec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
