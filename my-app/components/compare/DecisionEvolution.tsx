import ReactMarkdown from "react-markdown";
import { DecisionEvolution as DecisionEvolutionType } from "@/lib/compare";

export default function DecisionEvolution({ evolution }: { evolution: DecisionEvolutionType }) {
  if (!evolution || !evolution.reasoning) return null;
  const reasoningContent = Array.isArray(evolution.reasoning) 
    ? evolution.reasoning.join("\n") 
    : evolution.reasoning;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Deep Dive Reasoning
      </h3>
      <div className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed p-6 border border-border bg-card rounded-md">
        <ReactMarkdown>{reasoningContent || ""}</ReactMarkdown>
      </div>
    </div>
  );
}
