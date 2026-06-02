"use client";

import { cn } from "@/lib/utils";

export default function CenterCanvas({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={cn("h-full overflow-y-auto bg-background p-6 lg:p-10", className)}>
      <div className="max-w-3xl mx-auto space-y-8 pb-16">
        {children}
      </div>
    </div>
  );
}
