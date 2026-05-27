import { Users, Info } from "lucide-react";

export default function EvidenceConsensus({ consensus }: { consensus?: string }) {
  if (!consensus) return null;

  return (
    <div className="mb-8 p-4 rounded-md border border-primary/20 bg-primary/5 flex items-start space-x-3">
      <div className="mt-0.5">
        <Users className="w-5 h-5 text-primary" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-foreground flex items-center">
          Industry Consensus
          <Info className="w-3.5 h-3.5 text-muted-foreground ml-1.5" aria-label="Derived from external web sources" />
        </h4>
        <p className="text-sm text-foreground/80 mt-1">
          {consensus}
        </p>
      </div>
    </div>
  );
}
