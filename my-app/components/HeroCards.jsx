"use client";
import React, { useState, useEffect } from 'react';
import CardSwap, { Card } from "@/components/CardSwap";
import GlassIcons from "@/components/GlassIcons";
import { BrainCircuit, LineChart, FileDiff } from "lucide-react";

export default function HeroCards() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-[380px] h-[420px] rounded-3xl border border-white/10 bg-surface/40 backdrop-blur-xl animate-pulse flex flex-col items-center justify-center p-8 space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-white/5" />
        <div className="w-3/4 h-4 rounded bg-white/5" />
        <div className="w-1/2 h-3 rounded bg-white/5" />
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <CardSwap pauseOnHover={true} width={380} height={420} delay={4000}>
        {/* Feature 1 */}
        <Card className="flex flex-col items-center justify-center space-y-6 p-8 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-40 h-40 bg-primary/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
          <GlassIcons 
            className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
            items={[{ icon: <BrainCircuit className="w-8 h-8 text-white" />, color: 'blue', label: 'AI Decision Docs' }]} 
          />
          <p className="text-muted-foreground leading-relaxed text-center text-base mt-2 font-sans">
            Instant decision records with executive summaries, tradeoffs, and recommendations.
          </p>
        </Card>

        {/* Feature 2 */}
        <Card className="flex flex-col items-center justify-center space-y-6 p-8 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-500/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
          <GlassIcons 
            className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
            items={[{ icon: <LineChart className="w-8 h-8 text-white" />, color: 'green', label: 'Trust Metrics' }]} 
          />
          <p className="text-muted-foreground leading-relaxed text-center text-base mt-2 font-sans">
            Transparent confidence scores for evidence coverage and contradiction risk.
          </p>
        </Card>

        {/* Feature 3 */}
        <Card className="flex flex-col items-center justify-center space-y-6 p-8 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
          <GlassIcons 
            className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
            items={[{ icon: <FileDiff className="w-8 h-8 text-white" />, color: 'indigo', label: 'Architecture Diffs' }]} 
          />
          <p className="text-muted-foreground leading-relaxed text-center text-base mt-2 font-sans">
            Compare architectural research sessions side-by-side to highlight key tradeoffs.
          </p>
        </Card>
      </CardSwap>
      
      {/* Visual Pagination Indicator */}
      <div className="flex items-center gap-2 pt-2">
        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
        <span className="w-1.5 h-1.5 rounded-full bg-white/20" />
      </div>
    </div>
  );
}
