"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Copy, Check, UserCheck } from "lucide-react";

export function AccountIDBadge() {
  const { userId } = useAuth();
  const [copied, setCopied] = useState(false);

  if (!userId) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(userId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm">
      <div className="flex items-center gap-3.5">
        <div className="w-10 h-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
          <UserCheck className="w-5 h-5" />
        </div>
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Your Clerk User ID (Share with teammates to get invited)
          </p>
          <p className="text-sm font-mono text-foreground font-medium mt-0.5 select-all break-all">
            {userId}
          </p>
        </div>
      </div>
      <button
        onClick={handleCopy}
        type="button"
        className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-surface hover:bg-surface-hover border border-border/60 text-xs font-medium text-foreground transition-all shrink-0 active:scale-95"
      >
        {copied ? (
          <>
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            <span className="text-emerald-500 font-semibold">Copied ID!</span>
          </>
        ) : (
          <>
            <Copy className="w-3.5 h-3.5 text-muted-foreground" />
            <span>Copy ID</span>
          </>
        )}
      </button>
    </div>
  );
}
