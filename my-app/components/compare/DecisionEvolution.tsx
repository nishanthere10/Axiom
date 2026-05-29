import ReactMarkdown from "react-markdown";
import { DecisionEvolution as DecisionEvolutionType } from "@/lib/compare";

export default function DecisionEvolution({ evolution }: { evolution: DecisionEvolutionType }) {
  if (!evolution || !evolution.reasoning) return null;
  let reasoningContent = "";
  if (typeof evolution.reasoning === "string") {
    reasoningContent = evolution.reasoning;
  } else if (Array.isArray(evolution.reasoning)) {
    // If it's an array of strings, join them. If it's an array of objects, stringify.
    reasoningContent = typeof evolution.reasoning[0] === "string" 
      ? evolution.reasoning.join("\n\n") 
      : JSON.stringify(evolution.reasoning, null, 2);
  } else if (typeof evolution.reasoning === "object") {
    reasoningContent = JSON.stringify(evolution.reasoning, null, 2);
  }
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
