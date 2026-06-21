"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { useToast } from "./ToastProvider";

const ReactMarkdown = dynamic(() => import("react-markdown"), {
  ssr: false,
  loading: () => (
    <div className="animate-pulse space-y-2 py-2">
      <div className="h-3.5 bg-surface-hover rounded w-3/4" />
      <div className="h-3.5 bg-surface-hover rounded w-full" />
      <div className="h-3.5 bg-surface-hover rounded w-5/6" />
    </div>
  ),
});

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast("Copied to clipboard!", "success");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1.5 rounded-md bg-surface border border-white/5 text-muted-foreground hover:text-foreground hover:bg-surface-hover hover:border-white/20 transition-all z-10"
      aria-label="Copy code"
    >
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div
      className="
        prose prose-sm dark:prose-invert max-w-none leading-relaxed

        /* Base text */
        prose-p:text-foreground/90 prose-p:leading-7 prose-p:my-3

        /* Headings */
        prose-headings:text-foreground prose-headings:font-semibold prose-headings:tracking-tight
        prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-h3:uppercase prose-h3:tracking-widest prose-h3:text-muted-foreground

        /* Bold */
        prose-strong:text-foreground prose-strong:font-semibold

        /* Code — inline */
        prose-code:text-primary prose-code:bg-surface-hover prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-code:before:content-none prose-code:after:content-none

        /* Code blocks */
        prose-pre:bg-surface prose-pre:border prose-pre:border-border prose-pre:rounded-lg prose-pre:text-xs prose-pre:font-mono

        /* Lists */
        prose-ul:my-3 prose-ul:space-y-1 prose-li:text-foreground/90 prose-li:marker:text-primary/60
        prose-ol:my-3 prose-ol:space-y-1

        /* Blockquote */
        prose-blockquote:border-l-primary/50 prose-blockquote:text-muted-foreground prose-blockquote:not-italic

        /* Links */
        prose-a:text-primary prose-a:no-underline hover:prose-a:underline

        /* HR */
        prose-hr:border-border/50
      "
    >
      <ReactMarkdown
          components={{
            pre({ node, children, ...props }: any) {
              // Extract the raw text from the abstract syntax tree (AST) to perfectly preserve newlines and formatting.
              const extractText = (astNode: any): string => {
                if (astNode.type === "text") return astNode.value || "";
                if (astNode.children) return astNode.children.map(extractText).join("");
                return "";
              };
              const text = node ? extractText(node) : "";

              return (
                <div className="relative group">
                  <pre {...props} className={`${props.className || ""} pr-12`}>
                    {children}
                  </pre>
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <CopyButton text={text.replace(/\n$/, "")} />
                  </div>
                </div>
              );
            }
          }}
        >
          {content}
        </ReactMarkdown>
    </div>
  );
}
