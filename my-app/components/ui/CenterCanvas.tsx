"use client";

import { cn } from "@/lib/utils";

export default function CenterCanvas({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("h-full overflow-y-auto bg-background", className)}>
      <div className="max-w-3xl mx-auto px-6 py-8 lg:px-10 lg:py-10 space-y-8 pb-20">
        {children}
      </div>
    </div>
  );
}
