"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { ArchitectureDiagramSpec } from "@/lib/visuals";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  fontFamily: "inherit"
});

let mermaidCounter = 0;

export default function ArchitectureDiagramRenderer({ spec }: { spec: ArchitectureDiagramSpec }) {
  const [svgStr, setSvgStr] = useState<string>("");
  const [error, setError] = useState<boolean>(false);
  const hasRendered = useRef(false);
  const idRef = useRef(`mermaid-${++mermaidCounter}`);

  useEffect(() => {
    // Prevent double-render in React Strict Mode
    if (hasRendered.current) return;

    let isMounted = true;
    const id = idRef.current;

    const renderDiagram = async () => {
      try {
        // Strip markdown codeblocks if LLM accidentally included them
        let cleanSyntax = spec.mermaid_syntax
          .replace(/^```mermaid\n?/g, "")
          .replace(/```$/g, "")
          .trim();
          
        // Auto-fix LLM hallucinations where it appends an extra > to the end of a label
        cleanSyntax = cleanSyntax.replace(/-->\s*\|([^|]+)\|\s*>/g, '-->|$1|');
        
        // Auto-fix LLM hallucinations where it uses nested shapes like NodeID[A(Label)]
        cleanSyntax = cleanSyntax.replace(/\[\w*\(([^)]+)\)\]/g, '["$1"]');

        // Clean up any leftover mermaid element from a previous failed render
        const existing = document.getElementById(id);
        if (existing) existing.remove();
          
        const { svg } = await mermaid.render(id, cleanSyntax);
        if (isMounted) {
          hasRendered.current = true;
          setSvgStr(svg);
          setError(false);
        }
      } catch (err) {
        console.error("Mermaid render error:", err);
        // Clean up the broken element mermaid left in the DOM
        const broken = document.getElementById(id);
        if (broken) broken.remove();
        if (isMounted) {
          hasRendered.current = true;
          setError(true);
        }
      }
    };
    
    renderDiagram();
    return () => { isMounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spec.mermaid_syntax]);

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
      <h4 className="font-semibold text-lg">{spec.title}</h4>
      
      <div className="overflow-x-auto p-4 bg-background/50 rounded-lg flex justify-center min-h-[200px] items-center border border-border/50">
        {error ? (
          <div className="text-destructive text-sm flex flex-col items-center gap-2">
            <span>Failed to render architecture diagram.</span>
            <pre className="text-xs opacity-50 max-w-full overflow-x-auto">{spec.mermaid_syntax}</pre>
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
