"use client";

import { useEffect, useRef, useState, useId } from "react";
import mermaid from "mermaid";
import { ArchitectureDiagramSpec } from "@/lib/visuals";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  fontFamily: "inherit",
  flowchart: {
    nodeSpacing: 60,
    rankSpacing: 80,
    curve: "basis",
    padding: 20
  },
  themeVariables: {
    primaryColor: "#1c1917", // stone-900
    primaryTextColor: "#d6d3d1", // stone-300
    primaryBorderColor: "#44403c", // stone-700
    lineColor: "#78716c", // stone-500
    secondaryColor: "#292524", // stone-800
    tertiaryColor: "#1c1917",
    clusterBkg: "#1c1917", // subgraphs
    clusterBorder: "#44403c",
    fontSize: "14px"
  }
});

/**
 * Comprehensive sanitizer for LLM-generated Mermaid syntax.
 * Handles the most common hallucinations and formatting errors.
 */
function sanitizeMermaid(raw: string): string {
  let s = raw;

  // 0. Handle escaped JSON newlines and carriage returns
  s = s.replace(/\\n/g, '\n');
  s = s.replace(/\\r/g, '');

  // 1. Strip markdown code fences
  s = s.replace(/^```(?:mermaid)?\s*\n?/g, "");
  s = s.replace(/\n?```\s*$/g, "");
  s = s.trim();

  // 2. Remove trailing periods, commas, semicolons at end of lines
  s = s.replace(/([^\s])[.,;]+\s*$/gm, "$1");

  // 3. Fix LLM arrow hallucinations (e.g. -->|label|>)
  s = s.replace(/-->\s*\|([^|]+)\|\s*>/g, '-->|$1|');
  s = s.replace(/\|>\s/g, "| ");
  s = s.replace(/\|->\s/g, "| ");

  // 4. Fix nested node hallucinations e.g. A[Label(Text)] -> A["Label(Text)"]
  s = s.replace(/\[\w*\(([^)]+)\)\]/g, '["$1"]');

  // 5. Quote node labels containing special characters that break Mermaid
  s = s.replace(/\[([^\]"]+)\]/g, (match, content) => {
    if (/[()<>&;#{}]/.test(content)) {
      const escaped = content.replace(/"/g, "'");
      return `["${escaped}"]`;
    }
    return match;
  });

  // 6. Also fix round-bracket node labels: A(Label (stuff)) -> A("Label (stuff)")
  s = s.replace(/([A-Za-z0-9_]+)\((?!\()([^)]*[<>&;#].*?)\)/g, (_, id, content) => {
    const escaped = content.replace(/"/g, "'");
    return `${id}("${escaped}")`;
  });

  // 7. Remove HTML tags inside labels: A[<b>Text</b>] -> A["Text"]
  s = s.replace(/\[([^\]]*<[^>]+>[^\]]*)\]/g, (_, content) => {
    const stripped = content.replace(/<[^>]+>/g, "").trim();
    return `["${stripped}"]`;
  });

  // 8. Fix lines that end with just a period
  s = s.replace(/\.\s*$/gm, "");

  // 9. Ensure the diagram starts with a valid directive
  const firstLine = s.split("\n").find(l => l.trim().length > 0)?.trim() || "";
  const validStarters = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph|mindmap|timeline|journey|%%)/i;
  if (!validStarters.test(firstLine)) {
    s = "graph TD\n" + s;
  }

  return s.trim();
}

/**
 * Aggressive sanitizer — used as a fallback when the first render fails.
 */
function aggressiveSanitize(raw: string): string {
  let s = sanitizeMermaid(raw);

  // Quote ALL node labels to prevent any syntax issues
  s = s.replace(/\[([^\]"]+)\]/g, '["$1"]');

  // Remove any subgraph definitions that might be malformed
  s = s.replace(/subgraph\s+.*$/gm, "");
  s = s.replace(/^\s*end\s*$/gm, "");

  // Remove any style/class declarations that might be broken
  s = s.replace(/^\s*(style|classDef|class)\s+.*$/gm, "");

  // Remove click handlers
  s = s.replace(/^\s*click\s+.*$/gm, "");

  // Clean up empty lines
  s = s.replace(/\n{3,}/g, "\n\n");

  return s.trim();
}

export default function ArchitectureDiagramRenderer({ spec }: { spec: ArchitectureDiagramSpec }) {
  const [svgStr, setSvgStr] = useState<string>("");
  const [error, setError] = useState<boolean>(false);
  const hasRendered = useRef(false);
  
  // Bulletproof React ID Management: useId prevents Strict Mode collisions
  const reactId = useId();
  const mermaidId = `mermaid-${reactId.replace(/:/g, '')}`;

  useEffect(() => {
    if (hasRendered.current) return;

    let isMounted = true;
    const id = mermaidId;

    const tryRender = async (syntax: string, attempt: number): Promise<boolean> => {
      try {
        // Clean up any leftover mermaid element from a previous failed render
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const { svg } = await mermaid.render(id, syntax);
        if (isMounted) {
          hasRendered.current = true;
          setSvgStr(svg);
          setError(false);
        }
        return true;
      } catch (err) {
        console.warn(`Mermaid render attempt ${attempt} failed:`, err);
        const broken = document.getElementById(id);
        if (broken) broken.remove();
        return false;
      }
    };

    const renderDiagram = async () => {
      // Attempt 1: Standard sanitization
      const cleanSyntax = sanitizeMermaid(spec.mermaid_syntax);
      if (await tryRender(cleanSyntax, 1)) return;

      // Attempt 2: Aggressive sanitization
      const aggressiveSyntax = aggressiveSanitize(spec.mermaid_syntax);
      if (await tryRender(aggressiveSyntax, 2)) return;

      // All attempts failed
      if (isMounted) {
        console.error("Mermaid render failed after all attempts. Original syntax:", spec.mermaid_syntax);
        hasRendered.current = true;
        setError(true);
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
          <div id={mermaidId} dangerouslySetInnerHTML={{ __html: svgStr }} className="w-full flex justify-center" />
        ) : (
          <span className="text-muted-foreground text-sm animate-pulse uppercase tracking-widest font-semibold">
            Rendering Architecture...
          </span>
        )}
      </div>
    </div>
  );
}

