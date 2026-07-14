"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { Search, Loader2, BookMarked, FlaskConical, FolderKanban, Brain, ArrowRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

interface SearchResult {
  type: "research" | "decision" | "project" | "memory";
  id: string;
  title: string;
  subtitle: string;
  created_at: string;
  href: string;
}

interface Props {
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

const TYPE_ICONS = {
  research: <FlaskConical className="w-4 h-4 text-emerald-500" />,
  decision: <BookMarked className="w-4 h-4 text-blue-500" />,
  project: <FolderKanban className="w-4 h-4 text-amber-500" />,
  memory: <Brain className="w-4 h-4 text-purple-500" />,
};

export function WorkspaceSearchModal({ workspaceId, isOpen, onClose }: Props) {
  const router = useRouter();
  const { getToken } = useAuth();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      document.body.style.overflow = "hidden";
    } else {
      setQuery("");
      setResults([]);
      setSelectedIndex(0);
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  useEffect(() => {
    const fetchResults = async () => {
      if (!query || query.trim().length < 2) {
        setResults([]);
        return;
      }
      setLoading(true);
      try {
        const token = await getToken();
        if (!token) return;
        const res = await apiFetch<{ results: SearchResult[] }>(
          `/workspaces/${workspaceId}/search?q=${encodeURIComponent(query)}&limit=10`,
          token,
          { getToken }
        );
        setResults(res.results || []);
        setSelectedIndex(0);
      } catch (e) {
        console.error("Search failed", e);
      } finally {
        setLoading(false);
      }
    };
    const delay = setTimeout(fetchResults, 200);
    return () => clearTimeout(delay);
  }, [query, workspaceId, getToken]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % Math.max(results.length, 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + results.length) % Math.max(results.length, 1));
    } else if (e.key === "Enter" && results.length > 0) {
      e.preventDefault();
      const selected = results[selectedIndex];
      if (selected) {
        router.push(selected.href);
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-background/80 backdrop-blur-sm">
      <div className="absolute inset-0" onClick={onClose} />
      
      <div 
        className="relative w-full max-w-xl bg-background border border-border shadow-2xl rounded-xl overflow-hidden flex flex-col"
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center px-4 py-3 border-b border-border/50">
          <Search className="w-5 h-5 text-muted-foreground mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search decisions, research, memories..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-foreground text-sm focus:outline-none placeholder:text-muted-foreground"
          />
          {loading && <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />}
          <div className="ml-3 px-1.5 py-0.5 bg-surface text-[10px] text-muted-foreground rounded font-mono">
            ESC
          </div>
        </div>

        {results.length > 0 && (
          <div className="max-h-[60vh] overflow-y-auto py-2">
            {results.map((result, i) => (
              <button
                key={result.id}
                onClick={() => { router.push(result.href); onClose(); }}
                onMouseEnter={() => setSelectedIndex(i)}
                className={cn(
                  "w-full text-left flex items-start gap-3 px-4 py-3 transition-colors",
                  selectedIndex === i ? "bg-surface-hover" : "hover:bg-surface/50"
                )}
              >
                <div className="mt-0.5 bg-background border border-border p-1.5 rounded-md">
                  {TYPE_ICONS[result.type]}
                </div>
                <div className="flex-1 overflow-hidden">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="text-sm font-medium text-foreground truncate">
                      {result.title}
                    </p>
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                      {formatDistanceToNow(new Date(result.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {result.subtitle}
                  </p>
                </div>
                {selectedIndex === i && (
                  <ArrowRight className="w-4 h-4 text-muted-foreground self-center shrink-0" />
                )}
              </button>
            ))}
          </div>
        )}

        {query.length > 1 && results.length === 0 && !loading && (
          <div className="py-12 text-center text-sm text-muted-foreground">
            No results found for &quot;{query}&quot;
          </div>
        )}
      </div>
    </div>
  );
}
