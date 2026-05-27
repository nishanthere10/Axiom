import { StructuralDiff as DiffType } from "@/lib/compare";

export default function StructuralDiff({ diff }: { diff: DiffType }) {
  return (
    <div className="space-y-6">
      <div className="border-b border-border pb-2">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Structural Diff
        </h3>
      </div>
      
      <div className="space-y-4">
        {Object.entries(diff).map(([key, value]) => (
          <div key={key} className="space-y-2">
            <h4 className="text-xs font-medium uppercase text-muted-foreground">
              {key.replace("_", " ")}
            </h4>
            <pre className="p-4 rounded-md bg-[#1a1a1a] border border-[#333] text-sm overflow-x-auto whitespace-pre-wrap font-mono text-gray-300">
              {value}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
