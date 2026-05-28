import { SummaryCardSpec } from "@/lib/visuals";

export default function ResearchSummaryCardRenderer({ spec }: { spec: SummaryCardSpec }) {
  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
      <div className="space-y-1">
        <h4 className="font-semibold text-lg">{spec.title}</h4>
        <p className="text-sm text-muted-foreground">{spec.summary}</p>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-background/50 p-4 rounded-lg border border-border/50">
          <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold mb-1">Confidence</p>
          <p className="font-medium text-primary">{spec.confidence}</p>
        </div>
        <div className="bg-background/50 p-4 rounded-lg border border-border/50">
          <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold mb-1">Consensus</p>
          <p className="font-medium">{spec.consensus}</p>
        </div>
      </div>

      {spec.highlights && spec.highlights.length > 0 && (
        <div className="pt-4 border-t border-border/50">
          <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold mb-3">Key Highlights</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {spec.highlights.map((h, i) => (
              <div key={i} className="flex flex-col">
                <span className="text-xs text-muted-foreground">{h.label}</span>
                <span className="text-sm font-medium">{h.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
