"use client";

import dynamic from "next/dynamic";

const ReactMarkdown = dynamic(() => import("react-markdown"), {
  ssr: false, // Wait until client to render to avoid hydration mismatch if needed, but react-markdown supports SSR.
  // We keep SSR true by default unless we specifically want client-only rendering, but disabling SSR completely drops the chunk from the initial payload. 
  // Given we are fetching data client-side mostly in this app, ssr: false is fine and reduces bundle size.
  loading: () => <div className="animate-pulse space-y-2 py-2">
    <div className="h-4 bg-muted/50 rounded w-3/4"></div>
    <div className="h-4 bg-muted/50 rounded w-full"></div>
    <div className="h-4 bg-muted/50 rounded w-5/6"></div>
  </div>,
});

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
