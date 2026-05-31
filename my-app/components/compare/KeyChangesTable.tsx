import { memo } from "react";
import { KeyChange } from "@/lib/compare";

const badgeColors = {
  major: "bg-destructive/20 text-destructive border-destructive/50",
  minor: "bg-amber-500/20 text-amber-500 border-amber-500/50",
  improved: "bg-emerald-500/20 text-emerald-500 border-emerald-500/50",
  unchanged: "bg-muted text-muted-foreground border-border",
};

export default memo(function KeyChangesTable({ changes }: { changes: KeyChange[] }) {
  if (!changes || changes.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Key Architectural Changes
      </h3>
      <div className="border border-border rounded-md overflow-hidden bg-card">
        <table className="w-full text-sm text-left">
          <thead className="bg-muted/50 border-b border-border">
            <tr>
              <th className="px-4 py-3 font-medium text-foreground w-1/4">Dimension</th>
              <th className="px-4 py-3 font-medium text-foreground w-1/3">Baseline (Session A)</th>
              <th className="px-4 py-3 font-medium text-foreground w-1/3">New Direction (Session B)</th>
              <th className="px-4 py-3 font-medium text-foreground text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {changes.map((c, i) => (
              <tr key={i} className="group hover:bg-muted/30 transition-colors">
                <td className="px-4 py-4 align-top font-semibold text-foreground">
                  {c.field}
                </td>
                <td className="px-4 py-4 align-top text-muted-foreground">
                  {c.before}
                </td>
                <td className="px-4 py-4 align-top text-foreground font-medium">
                  {c.after}
                </td>
                <td className="px-4 py-4 align-top text-center">
                  <span
                    className={`px-2 py-1 text-xs font-semibold uppercase tracking-wider rounded-full border ${
                      badgeColors[c.change_type] || badgeColors.unchanged
                    }`}
                  >
                    {c.change_type}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});
