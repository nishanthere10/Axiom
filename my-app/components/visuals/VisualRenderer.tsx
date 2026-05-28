import { VisualSpec } from "@/lib/visuals";
import ArchitectureDiagramRenderer from "./ArchitectureDiagramRenderer";
import DecisionTreeRenderer from "./DecisionTreeRenderer";
import ResearchSummaryCardRenderer from "./ResearchSummaryCardRenderer";

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
