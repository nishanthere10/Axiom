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

/**
 * Comprehensive sanitizer for LLM-generated Mermaid syntax.
 * Handles the most common hallucinations and formatting errors.
 */
function sanitizeMermaid(raw: string): string {
  let s = raw;

  // 1. Strip markdown code fences
  s = s.replace(/^```(?:mermaid)?\s*\n?/g, "");
  s = s.replace(/\n?```\s*$/g, "");
  s = s.trim();

  // 2. Remove trailing periods, commas, semicolons at end of lines
  //    e.g. "E --> F[Target System]." → "E --> F[Target System]"
  s = s.replace(/([^\s])[.,;]+\s*$/gm, "$1");

  // 3. Fix trailing > after pipe labels: -->|label|> B → -->|label| B
  s = s.replace(/\|>\s/g, "| ");

  // 4. Fix trailing -> after pipe labels: -->|label|-> B → -->|label| B
  s = s.replace(/\|->\s/g, "| ");

  // 5. Quote node labels containing special characters that break Mermaid
  //    A[Label (Extra Info)] → A["Label (Extra Info)"]
  //    But don't double-quote: A["Already Quoted"] stays as-is
  s = s.replace(/\[([^\]"]+)\]/g, (match, content) => {
    // If content contains parentheses, angle brackets, ampersands, or other specials, quote it
    if (/[()<>&;#{}]/.test(content)) {
      // Escape any existing double quotes inside the label
      const escaped = content.replace(/"/g, "'");
      return `["${escaped}"]`;
    }
    return match;
  });

  // 6. Also fix round-bracket node labels: A(Label (stuff)) → A("Label (stuff)")
  //    Match single-paren nodes like A(label) but don't break A((label)) (stadium shape)
  s = s.replace(/([A-Za-z0-9_]+)\((?!\()([^)]*[<>&;#].*?)\)/g, (_, id, content) => {
    const escaped = content.replace(/"/g, "'");
    return `${id}("${escaped}")`;
  });

  // 7. Remove HTML tags inside labels: A[<b>Text</b>] → A["Text"]
  s = s.replace(/\[([^\]]*<[^>]+>[^\]]*)\]/g, (_, content) => {
    const stripped = content.replace(/<[^>]+>/g, "").trim();
    return `["${stripped}"]`;
  });

  // 8. Fix lines that end with just a period (no brackets)
  //    "D --> E." → "D --> E"
  s = s.replace(/\.\s*$/gm, "");

  // 9. Ensure the diagram starts with a valid directive
  //    If the first non-empty line isn't a known directive, prepend "graph TD"
  const firstLine = s.split("\n").find(l => l.trim().length > 0)?.trim() || "";
  const validStarters = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph|mindmap|timeline|journey|%%)/i;
  if (!validStarters.test(firstLine)) {
    s = "graph TD\n" + s;
  }

  return s.trim();
}

/**
 * Aggressive sanitizer — used as a fallback when the first render fails.
 * Strips everything down to the simplest possible valid syntax.
 */
function aggressiveSanitize(raw: string): string {
  let s = sanitizeMermaid(raw);

  // Quote ALL node labels to prevent any syntax issues
  s = s.replace(/\[([^\]"]+)\]/g, '["$1"]');

  // Remove any subgraph definitions that might be malformed
  // (keep the content but remove the subgraph wrapping)
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
  const idRef = useRef(`mermaid-${++mermaidCounter}`);

  useEffect(() => {
    if (hasRendered.current) return;

    let isMounted = true;
    const id = idRef.current;

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

