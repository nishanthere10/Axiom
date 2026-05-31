import { memo } from "react";
import { StructuralDiff as DiffType } from "@/lib/compare";

function renderDiffLine(line: string, index: number) {
  if (line.startsWith('+++') || line.startsWith('---')) {
    return <div key={index} className="text-muted-foreground font-bold py-1">{line}</div>;
  }
  if (line.startsWith('@@')) {
    return <div key={index} className="text-blue-400 py-1 opacity-70">{line}</div>;
  }
  if (line.startsWith('+')) {
    return <div key={index} className="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 my-0.5 rounded-sm">{line}</div>;
  }
  if (line.startsWith('-')) {
    return <div key={index} className="bg-rose-500/10 text-rose-400 px-2 py-0.5 my-0.5 rounded-sm">{line}</div>;
  }
  return <div key={index} className="px-2 py-0.5 text-gray-300">{line}</div>;
}

export default memo(function StructuralDiff({ diff }: { diff: DiffType }) {
  return (
    <div className="space-y-6">
      <div className="border-b border-border pb-2">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Structural Diff
        </h3>
      </div>
      
      <div className="space-y-4">
        {Object.entries(diff).map(([key, value]) => {
          if (!value) return null;
          const diffString = String(value);
          const lines = diffString.split('\n');
          
          return (
            <div key={key} className="space-y-2">
              <h4 className="text-xs font-medium uppercase text-muted-foreground">
                {key.replace("_", " ")}
              </h4>
              <div className="p-4 rounded-md bg-[#1a1a1a] border border-[#333] text-sm overflow-x-auto whitespace-pre-wrap font-mono">
                {lines.map((line, index) => renderDiffLine(line, index))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});
