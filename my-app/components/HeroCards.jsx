"use client";
import React, { useState, useEffect } from 'react';
import CardSwap, { Card } from "@/components/CardSwap";
import GlassIcons from "@/components/GlassIcons";
import { BrainCircuit, LineChart, FileDiff } from "lucide-react";
import Loader from "@/components/loader";

export default function HeroCards() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-full h-[500px] flex items-center justify-center">
        <Loader />
      </div>
    );
  }

  return (
    <CardSwap pauseOnHover={true} width={400} height={450} delay={4000}>
      {/* Feature 1 */}
      <Card className="flex flex-col items-center justify-center space-y-6 p-10 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
        <div className="absolute top-0 right-0 w-40 h-40 bg-primary/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
        <GlassIcons 
          className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
          items={[{ icon: <BrainCircuit className="w-8 h-8 text-white" />, color: 'blue', label: 'AI Deep Dives' }]} 
        />
        <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4 font-sans">
          Generate extensive decision documents covering executive summaries, alternatives, and tradeoffs instantly.
        </p>
      </Card>

      {/* Feature 2 */}
      <Card className="flex flex-col items-center justify-center space-y-6 p-10 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
        <div className="absolute top-0 right-0 w-40 h-40 bg-emerald-500/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
        <GlassIcons 
          className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
          items={[{ icon: <LineChart className="w-8 h-8 text-white" />, color: 'green', label: 'Decision Evolution' }]} 
        />
        <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4 font-sans">
          Track how your architecture choices evolve over time with detailed reasoning and confidence scoring.
        </p>
      </Card>

      {/* Feature 3 */}
      <Card className="flex flex-col items-center justify-center space-y-6 p-10 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
        <div className="absolute top-0 right-0 w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
        <GlassIcons 
          className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
          items={[{ icon: <FileDiff className="w-8 h-8 text-white" />, color: 'indigo', label: 'Structural Diffs' }]} 
        />
        <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4 font-sans">
          Compare saved research sessions side-by-side to understand exactly what changed between two approaches.
        </p>
      </Card>
    </CardSwap>
  );
}
