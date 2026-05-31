import { VisualSpec } from "@/lib/visuals";
import dynamic from "next/dynamic";

const ArchitectureDiagramRenderer = dynamic(() => import("./ArchitectureDiagramRenderer"), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted/50 rounded-xl min-h-[200px] flex items-center justify-center border border-border/50"><span className="text-muted-foreground text-sm uppercase tracking-widest font-medium">Loading Visual...</span></div>
});
const DecisionTreeRenderer = dynamic(() => import("./DecisionTreeRenderer"), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted/50 rounded-xl min-h-[200px] flex items-center justify-center border border-border/50"><span className="text-muted-foreground text-sm uppercase tracking-widest font-medium">Loading Visual...</span></div>
});
const ResearchSummaryCardRenderer = dynamic(() => import("./ResearchSummaryCardRenderer"), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted/50 rounded-xl min-h-[200px] flex items-center justify-center border border-border/50"><span className="text-muted-foreground text-sm uppercase tracking-widest font-medium">Loading Visual...</span></div>
});

export default function VisualRenderer({ visuals }: { visuals: VisualSpec[] }) {
  if (!visuals || visuals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      {visuals.map((spec, index) => {
        switch (spec.type) {
          case "architecture_diagram":
            return <ArchitectureDiagramRenderer key={index} spec={spec} />;
          case "decision_tree":
            return <DecisionTreeRenderer key={index} spec={spec} />;
          case "summary_card":
            return <ResearchSummaryCardRenderer key={index} spec={spec} />;
          default:
            return null; // Ignore unknown types
        }
      })}
    </div>
  );
}
