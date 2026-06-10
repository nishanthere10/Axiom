import { Users, Info } from "lucide-react";

export default function EvidenceConsensus({ consensus }: { consensus?: string }) {
  if (!consensus) return null;

  return (
    <div className="p-3 rounded-lg border border-primary/20 bg-primary/5 flex items-start gap-3">
      <Users className="w-4 h-4 text-primary shrink-0 mt-0.5" />
      <div className="space-y-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <h4 className="text-xs font-semibold text-foreground">Industry Consensus</h4>
          <Info className="w-3 h-3 text-muted-foreground" aria-label="Derived from external web sources" />
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">{consensus}</p>
      </div>
    </div>
  );
}
