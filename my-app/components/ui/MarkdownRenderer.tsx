"use client";

import dynamic from "next/dynamic";

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
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
