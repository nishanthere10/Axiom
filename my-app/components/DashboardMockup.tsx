"use client";

import { CheckCircle2, Copy, ShieldCheck, TerminalSquare } from "lucide-react";

export default function DashboardMockup() {
  return (
    <div className="w-full max-w-6xl mx-auto mt-16 min-h-[648px] rounded-2xl border border-white/10 bg-background/80 backdrop-blur-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-1000 fill-mode-both">
      {/* Window Header */}
      <div className="h-12 border-b border-white/10 flex items-center px-4 bg-surface/50">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-amber-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <div className="flex-1 flex justify-center">
          <div className="px-4 py-1 rounded-md bg-background border border-white/5 text-xs text-muted-foreground font-mono flex items-center gap-2 shadow-inner">
            <TerminalSquare className="w-3 h-3" />
            axiom_workspace_749.json
          </div>
        </div>
        <div className="w-[52px]" /> {/* Spacer for centering */}
      </div>

      {/* Main Content Area */}
      <div className="flex flex-col md:flex-row h-[600px]">
        {/* Sidebar Mockup */}
        <div className="hidden md:flex flex-col w-64 border-r border-white/10 bg-surface/30 p-4 space-y-4">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-2">History</div>
          <div className="space-y-1">
            <div className="px-3 py-2 rounded-md bg-primary/10 border border-primary/20 text-primary text-sm font-medium">
              High-write Event Log
            </div>
            <div className="px-3 py-2 rounded-md hover:bg-surface-hover text-muted-foreground text-sm cursor-pointer transition-colors">
              User Auth Microservice
            </div>
            <div className="px-3 py-2 rounded-md hover:bg-surface-hover text-muted-foreground text-sm cursor-pointer transition-colors">
              Payment Gateway Caching
            </div>
          </div>
        </div>

        {/* Editor/Renderer Mockup */}
        <div className="flex-1 flex flex-col bg-background relative overflow-hidden">
          
          {/* Top toolbar */}
          <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 shrink-0">
            <h2 className="font-display font-semibold text-lg flex items-center gap-2">
              Architecture Decision
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-xs font-mono font-bold ml-2">
                APPROVED
              </span>
            </h2>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5 text-emerald-500 text-sm font-medium">
                <ShieldCheck className="w-4 h-4" />
                98% Confidence
              </div>
              <button className="p-2 hover:bg-surface rounded-md text-muted-foreground transition-colors">
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Document Content */}
          <div className="flex-1 p-8 overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background z-10 pointer-events-none" />
            
            <div className="space-y-6 opacity-90 max-w-3xl">
              <h1 className="text-3xl font-bold border-b border-white/10 pb-4">
                PostgreSQL vs MongoDB for High-Write Logs
              </h1>
              
              <div className="space-y-4">
                <h3 className="text-xl font-semibold text-primary">1. Context & Problem Statement</h3>
                <p className="text-muted-foreground leading-relaxed">
                  The system requires ingesting 50,000 events per second. The previous architecture utilized a monolithic PostgreSQL instance which suffered from severe write-lock contention during peak loads.
                </p>
              </div>

              <div className="space-y-4 pt-4">
                <h3 className="text-xl font-semibold text-primary">2. Decision</h3>
                <p className="text-foreground leading-relaxed">
                  We will migrate the event logging subsystem to <strong className="text-primary">ClickHouse</strong> instead of MongoDB or PostgreSQL.
                </p>
              </div>

              <div className="space-y-4 pt-4">
                <h3 className="text-xl font-semibold text-primary">3. Justification</h3>
                <ul className="space-y-3 text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                    <span><strong>Throughput:</strong> ClickHouse utilizes a column-oriented storage engine capable of millions of inserts per second without locking overhead.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                    <span><strong>Compression:</strong> Log data is highly repetitive. ClickHouse LZ4/ZSTD compression yields a 70% storage reduction over MongoDB BSON.</span>
                  </li>
                </ul>
              </div>

              <div className="pt-8">
                {/* Simulated code block */}
                <div className="rounded-md bg-surface border border-white/5 p-4 font-mono text-sm text-blue-300">
                  <span className="text-pink-400">CREATE TABLE</span> event_logs (<br/>
                  &nbsp;&nbsp;timestamp DateTime,<br/>
                  &nbsp;&nbsp;user_id UInt32,<br/>
                  &nbsp;&nbsp;action String<br/>
                  ) <span className="text-pink-400">ENGINE</span> = MergeTree()<br/>
                  <span className="text-pink-400">ORDER BY</span> (timestamp, user_id);
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
