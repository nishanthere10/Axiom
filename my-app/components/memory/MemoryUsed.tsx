"use client";

interface MemoryContext {
  preferences: { value: string; reason: string }[];
  historical_patterns: string[];
  related_decisions: string[];
  consistency_warnings: string[];
}

export default function MemoryUsed({ context }: { context: MemoryContext }) {
  if (!context) return null;
  
  const hasMemories = 
    (context.preferences && context.preferences.length > 0) || 
    (context.historical_patterns && context.historical_patterns.length > 0) ||
    (context.related_decisions && context.related_decisions.length > 0) ||
    (context.consistency_warnings && context.consistency_warnings.length > 0);

  if (!hasMemories) return null;

  return (
    <div className="bg-secondary/30 rounded-xl p-5 space-y-4 border border-secondary">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          🧠 Memory Influence
        </span>
      </div>

      {context.consistency_warnings && context.consistency_warnings.length > 0 && (
        <div className="bg-destructive/10 text-destructive p-3 rounded border border-destructive/20 text-sm space-y-1">
          <p className="font-semibold text-xs uppercase tracking-widest">Consistency Warning</p>
          <ul className="list-disc pl-4">
            {context.consistency_warnings.map((warn, i) => <li key={i}>{warn}</li>)}
          </ul>
        </div>
      )}

      {context.preferences && context.preferences.length > 0 && (
        <div className="text-sm space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">Preferences Applied</p>
          <ul className="list-disc pl-4 text-foreground/80">
            {context.preferences.map((pref, i) => (
              <li key={i}><span className="font-medium text-foreground">{pref.value}</span>: {pref.reason}</li>
            ))}
          </ul>
        </div>
      )}

      {context.related_decisions && context.related_decisions.length > 0 && (
        <div className="text-sm space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">Related History</p>
          <ul className="list-disc pl-4 text-foreground/80">
            {context.related_decisions.map((dec, i) => <li key={i}>{dec}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
