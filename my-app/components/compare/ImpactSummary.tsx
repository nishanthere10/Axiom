import { memo } from "react";
import { ImpactSummary as ImpactSummaryType } from "@/lib/compare";

const riskColors = {
  low: "bg-emerald-500/20 text-emerald-500 border-emerald-500/50",
  medium: "bg-amber-500/20 text-amber-500 border-amber-500/50",
  high: "bg-destructive/20 text-destructive border-destructive/50",
};

export default memo(function ImpactSummary({ impact }: { impact: ImpactSummaryType }) {
  if (!impact) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Impact & Action Items
      </h3>
      <div className="border border-border rounded-md bg-card p-6 space-y-6">
        
        {/* Top Info Row */}
        <div className="flex flex-wrap gap-4 items-center border-b border-border pb-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Risk Level:</span>
            <span
              className={`px-3 py-1 text-xs font-bold uppercase tracking-widest rounded-full border ${
                riskColors[impact.risk_level] || riskColors.medium
              }`}
            >
              {impact.risk_level}
            </span>
          </div>
          
          <div className="h-4 w-px bg-border hidden sm:block" />
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Migration Needed:</span>
            <span className={`text-sm font-semibold ${impact.migration_needed ? 'text-amber-500' : 'text-emerald-500'}`}>
              {impact.migration_needed ? "Yes" : "No"}
            </span>
          </div>
          
          <div className="h-4 w-px bg-border hidden sm:block" />
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Breaking Changes:</span>
            <span className={`text-sm font-semibold ${impact.breaking_changes ? 'text-destructive' : 'text-emerald-500'}`}>
              {impact.breaking_changes ? "Yes" : "No"}
            </span>
          </div>
        </div>

        {/* Action Items List */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-foreground">Recommended Actions</h4>
          <ul className="space-y-2">
            {impact.action_items?.map((item, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-muted-foreground items-start">
                <span className="flex-shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary text-xs font-bold mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
        
      </div>
    </div>
  );
});
