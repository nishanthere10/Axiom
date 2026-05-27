"use client";

import { useEffect, useState } from "react";

interface Props {
  isComplete: boolean;
}

const STATES = [
  "Comparing Decisions...",
  "Analyzing Differences...",
  "Explaining Decision Changes...",
  "Generating Impact...",
  "Complete"
];

export default function ComparisonProgress({ isComplete }: Props) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (isComplete) {
      setIndex(STATES.length - 1);
      return;
    }

    const interval = setInterval(() => {
      setIndex((prev) => (prev < STATES.length - 2 ? prev + 1 : prev));
    }, 4000);

    return () => clearInterval(interval);
  }, [isComplete]);

  const currentStatus = STATES[index];

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      <div className="flex justify-between items-end text-sm">
        <span className="text-muted-foreground uppercase tracking-wider text-xs font-semibold">
          Status
        </span>
        <span className="text-foreground animate-pulse">{currentStatus}</span>
      </div>
      <div className="h-1 w-full bg-secondary overflow-hidden rounded-full">
        <div 
          className="h-full bg-primary transition-all duration-1000 ease-out" 
          style={{ width: isComplete ? "100%" : `${(index / (STATES.length - 1)) * 100}%` }}
        />
      </div>
    </div>
  );
}
