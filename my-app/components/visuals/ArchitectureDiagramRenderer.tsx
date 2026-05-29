"use client";

import { useEffect, useState } from "react";
import mermaid from "mermaid";
import { ArchitectureDiagramSpec } from "@/lib/visuals";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  fontFamily: "inherit"
});

export default function ArchitectureDiagramRenderer({ spec }: { spec: ArchitectureDiagramSpec }) {
  const [svgStr, setSvgStr] = useState<string>("");
  const [error, setError] = useState<boolean>(false);
  
  // We use a stable ID based on title or random fallback to avoid hydration mismatches 
  // but since we render on client side entirely, it's safer.
  const id = "mermaid-diagram-" + Math.random().toString(36).substring(2, 9);

  useEffect(() => {
    let isMounted = true;
    const renderDiagram = async () => {
      try {
        // Strip markdown codeblocks if LLM accidentally included them
        let cleanSyntax = spec.mermaid_syntax
          .replace(/^```mermaid\n?/g, "")
          .replace(/```$/g, "")
          .trim();
          
        // Auto-fix LLM hallucinations where it appends an extra > to the end of a label
        cleanSyntax = cleanSyntax.replace(/-->\s*\|([^|]+)\|\s*>/g, '-->|$1|');
          
        const { svg } = await mermaid.render(id, cleanSyntax);
        if (isMounted) {
          setSvgStr(svg);
          setError(false);
        }
      } catch (err) {
        console.error("Mermaid render error:", err);
        if (isMounted) setError(true);
      }
    };
    
    renderDiagram();
    return () => { isMounted = false; };
  }, [spec.mermaid_syntax, id]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <h4 className="font-semibold text-lg">{spec.title}</h4>
      
      <div className="overflow-x-auto p-4 bg-background/50 rounded-lg flex justify-center min-h-[200px] items-center border border-border/50">
        {error ? (
          <div className="text-destructive text-sm flex flex-col items-center gap-2">
            <span>Failed to render architecture diagram.</span>
            <pre className="text-xs opacity-50">{spec.mermaid_syntax}</pre>
          </div>
        ) : svgStr ? (
          <div dangerouslySetInnerHTML={{ __html: svgStr }} className="w-full flex justify-center" />
        ) : (
          <span className="text-muted-foreground text-sm animate-pulse uppercase tracking-widest font-semibold">
            Rendering Architecture...
          </span>
        )}
      </div>
    </div>
  );
}
