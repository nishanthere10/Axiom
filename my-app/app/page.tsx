import Link from "next/link";
import { ArrowRight, Box, ShieldCheck, Zap, Layers, RefreshCcw, FileText, GitBranch, Network, Scale } from "lucide-react";
import Footer from "@/components/ui/Footer";
import HeroCards from "@/components/HeroCards";
import DashboardMockup from "@/components/DashboardMockup";
import FaqSection from "@/components/FaqSection";
import LandingLoaderWrapper from "@/components/LandingLoaderWrapper";
import Aurora from "@/components/Aurora";

export default function Home() {
  return (
    <LandingLoaderWrapper>
      <main className="h-full w-full overflow-y-auto bg-background selection:bg-primary/30 relative font-sans">
      {/* ── Ultra-fast, lightweight 5-color WebGL Aurora Background ── */}
      <div className="absolute top-0 left-0 right-0 z-0 pointer-events-none h-[110vh] overflow-hidden opacity-90">
        <Aurora 
          colorStops={["#020617", "#1e3a8a", "#2563eb", "#38bdf8", "#00f2fe"]} 
          amplitude={1.6}
          blend={0.85}
          speed={0.5}
        />
      </div>
      
      {/* Subtle fade to blend background into the page body */}
      <div className="absolute top-0 left-0 right-0 h-[110vh] bg-gradient-to-b from-transparent via-background/20 to-background pointer-events-none z-10" />

      <div className="flex flex-col min-h-full relative z-20">
        
        {/* =========================================
            HERO SECTION
           ========================================= */}
        <header className="w-full min-h-[85vh] px-10 sm:px-16 md:px-24 lg:px-48 max-w-[140rem] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center py-24 lg:py-36 relative">
          
          {/* Radial glow orbs behind headline */}
          <div className="absolute top-1/2 left-24 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/15 rounded-full blur-[120px] pointer-events-none" />
          <div className="absolute top-1/3 left-48 w-[300px] h-[300px] bg-indigo-500/10 rounded-full blur-[80px] pointer-events-none" />

          {/* Left Column: Text Content */}
          <div className="flex flex-col justify-center items-start text-left space-y-8 max-w-2xl min-h-[450px] w-full">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-white/5 border border-white/10 backdrop-blur-md text-primary text-xs font-mono uppercase tracking-widest shadow-2xl shadow-primary/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              AI Decision Engine · v1.0
            </div>
            
            {/* Display font used for maximum impact */}
            <h1 className="text-5xl md:text-6xl lg:text-[4.5rem] font-display font-bold tracking-tight text-foreground leading-[1.1] drop-shadow-2xl text-balance">
              The smartest way to research{" "}
              <span className="font-mono font-light tracking-tight italic text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-primary to-blue-300">
                system architecture.
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground animate-in fade-in slide-in-from-bottom-8 duration-700 delay-500 fill-mode-both font-medium max-w-xl">
              Stop guessing. Generate comprehensive decision documents, track architectural evolution, and compare tradeoffs instantly with AI.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-700 fill-mode-both">
              <Link 
                href="/workspaces"
                className="group relative inline-flex items-center justify-center gap-3 rounded-md bg-primary px-8 py-3.5 text-sm font-semibold text-primary-foreground shadow-[0_0_40px_-8px_rgba(59,130,246,0.7)] hover:shadow-[0_0_60px_-8px_rgba(59,130,246,0.9)] hover:scale-[1.02] transition-all duration-500"
              >
                Initialize Workspace
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
              <Link 
                href="/research-documents"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-white/[0.06] backdrop-blur-md px-8 py-3.5 text-sm font-mono text-foreground/90 hover:bg-white/[0.10] border border-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-all duration-300"
              >
                [View_Examples]
              </Link>
            </div>
          </div>

          {/* Right Column: CardSwap */}
          <div className="relative w-full min-h-[450px] flex flex-col justify-center items-center animate-in fade-in zoom-in-95 duration-1000 delay-300 fill-mode-both">
            <HeroCards />
          </div>
        </header>

        {/* Social Proof Strip */}
        <div className="w-full border-y border-white/10 bg-white/[0.03] backdrop-blur-sm py-5 px-8 flex flex-wrap items-center justify-center gap-8 md:gap-16 text-xs text-muted-foreground font-mono">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_2px_rgba(52,211,153,0.5)]" />
            <span className="font-semibold text-foreground/70">8 Parallel Research Nodes</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_6px_2px_rgba(96,165,250,0.5)]" />
            <span className="font-semibold text-foreground/70">Multi-Model Evidence Scoring</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_6px_2px_rgba(129,140,248,0.5)]" />
            <span className="font-semibold text-foreground/70">100% Stateless &amp; Private</span>
          </div>
        </div>

        {/* =========================================
            HOW IT WORKS SECTION 
           ========================================= */}
        <section aria-label="How it works" className="w-full bg-surface/30 border-b border-white/5 py-24 px-10 sm:px-16 md:px-24 lg:px-48">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="text-center space-y-4">
              <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight">How Atlas Works</h2>
              <p className="text-primary font-mono text-sm uppercase tracking-widest">// The Research Pipeline</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
              {/* Step 1 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-surface/60 backdrop-blur-sm border border-white/8 rounded-xl hover:border-primary/50 hover:shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)] transition-all group shadow-xl">
                <div className="w-14 h-14 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500 relative">
                  <Box className="w-6 h-6 text-primary" />
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-primary-foreground font-mono text-xs font-bold flex items-center justify-center">1</span>
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">Define Decision</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  Input your architectural dilemma. Atlas decomposes the problem into research axes and identifies constraints.
                </p>
              </div>

              {/* Step 2 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-surface/60 backdrop-blur-sm border border-white/8 rounded-xl hover:border-primary/50 hover:shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)] transition-all group shadow-xl">
                <div className="w-14 h-14 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500 relative">
                  <RefreshCcw className="w-6 h-6 text-primary" />
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-primary-foreground font-mono text-xs font-bold flex items-center justify-center">2</span>
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">Evidence Synthesis</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  Runs 8 parallel research nodes — memory graph search, codebase indexing, web evidence scoring, and contradiction detection.
                </p>
              </div>

              {/* Step 3 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-surface/60 backdrop-blur-sm border border-white/8 rounded-xl hover:border-primary/50 hover:shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)] transition-all group shadow-xl">
                <div className="w-14 h-14 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500 relative">
                  <Zap className="w-6 h-6 text-primary" />
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary text-primary-foreground font-mono text-xs font-bold flex items-center justify-center">3</span>
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">Decision Record</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  Delivers a complete decision document: recommendation, tradeoff matrix, confidence breakdown, and Mermaid diagrams.
                </p>
              </div>
            </div>

            {/* DASHBOARD MOCKUP */}
            <div className="pt-16 pb-8">
              <div className="text-center space-y-4 mb-12">
                <h2 className="text-2xl md:text-3xl font-display font-bold tracking-tight">Don't just take our word for it.</h2>
                <p className="text-muted-foreground">See the interface in action.</p>
              </div>
              <DashboardMockup />
            </div>

          </div>
        </section>

        {/* =========================================
            FEATURE ARSENAL (BENTO GRID)
           ========================================= */}
        <section aria-label="Feature Arsenal" className="w-full py-24 px-10 sm:px-16 md:px-24 lg:px-48">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="text-left space-y-4">
              <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight">Feature Arsenal</h2>
              <p className="text-primary font-mono text-sm uppercase tracking-widest">// Enterprise Grade Tools</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              
              {/* Bento Item 1: Large */}
              <div className="lg:col-span-2 relative group overflow-hidden rounded-2xl bg-surface/80 backdrop-blur-sm border border-white/8 p-8 flex flex-col justify-end hover:border-primary/50 transition-all shadow-xl min-h-[260px]">
                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent z-0" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent z-10" />
                <div className="absolute top-6 right-6 text-white/10 group-hover:text-primary/20 transition-colors z-0">
                  <Layers className="w-36 h-36" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-bold font-display">Versioned Memory Graph</h3>
                  <p className="text-muted-foreground text-sm max-w-md">
                    Atlas extracts and remembers historical decisions, team preferences, and constraints across sessions to build persistent context.
                  </p>
                </div>
              </div>

              {/* Bento Item 2 */}
              <div className="relative group overflow-hidden rounded-2xl bg-surface/80 backdrop-blur-sm border border-white/8 p-8 flex flex-col justify-end hover:border-emerald-500/50 transition-all shadow-xl min-h-[260px]">
                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent z-0" />
                <div className="absolute top-6 right-6 text-white/10 group-hover:text-emerald-500/20 transition-colors z-0">
                  <ShieldCheck className="w-28 h-28" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-bold font-display">Trust Scoring</h3>
                  <p className="text-muted-foreground text-sm">
                    4-axis transparent confidence scoring for source quality, coverage, contradiction risk, and overall decision strength.
                  </p>
                </div>
              </div>

              {/* Bento Item 3 */}
              <div className="relative group overflow-hidden rounded-2xl bg-surface/80 backdrop-blur-sm border border-white/8 p-8 flex flex-col justify-end hover:border-indigo-500/50 transition-all shadow-xl min-h-[260px]">
                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent z-0" />
                <div className="absolute top-6 right-6 text-white/10 group-hover:text-indigo-500/20 transition-colors z-0">
                  <Scale className="w-28 h-28" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-bold font-display">Compare Engine</h3>
                  <p className="text-muted-foreground text-sm">
                    Side-by-side structural comparison of two past research sessions to highlight tradeoffs and metric diffs.
                  </p>
                </div>
              </div>

              {/* Bento Item 4 */}
              <div className="relative group overflow-hidden rounded-2xl bg-surface/80 backdrop-blur-sm border border-white/8 p-8 flex flex-col justify-end hover:border-blue-500/50 transition-all shadow-xl min-h-[260px]">
                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent z-0" />
                <div className="absolute top-6 right-6 text-white/10 group-hover:text-blue-500/20 transition-colors z-0">
                  <GitBranch className="w-28 h-28" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-bold font-display">Codebase Context</h3>
                  <p className="text-muted-foreground text-sm">
                    Indexes your GitHub repo structure and doc files to evaluate choices against your actual codebase architecture.
                  </p>
                </div>
              </div>

              {/* Bento Item 5: Large */}
              <div className="lg:col-span-2 relative group overflow-hidden rounded-2xl bg-surface/80 backdrop-blur-sm border border-white/8 p-8 flex flex-col justify-end hover:border-purple-500/50 transition-all shadow-xl min-h-[260px]">
                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent z-0" />
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent z-10" />
                <div className="absolute top-6 right-6 text-white/10 group-hover:text-purple-500/20 transition-colors z-0">
                  <Network className="w-36 h-36" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-bold font-display">Auto Diagram Specs</h3>
                  <p className="text-muted-foreground text-sm max-w-md">
                    Generates clean Mermaid sequence and architecture diagrams automatically alongside every decision document.
                  </p>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* =========================================
            FAQ SECTION
           ========================================= */}
        <FaqSection />

        {/* =========================================
            FINAL PUSH CTA
           ========================================= */}
        <section aria-label="Get Started CTA" className="w-full py-32 px-10 sm:px-16 md:px-24 lg:px-48 border-t border-white/5 bg-background relative overflow-hidden">
          <div className="absolute inset-0 bg-primary/5 pointer-events-none" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-primary/20 blur-[120px] rounded-full pointer-events-none" />
          
          <div className="max-w-4xl mx-auto relative z-10 bg-surface/50 backdrop-blur-2xl border border-white/10 rounded-3xl p-12 md:p-20 text-center space-y-8 shadow-2xl animate-in fade-in zoom-in-95 duration-1000">
            <h2 className="text-4xl md:text-6xl font-display font-bold tracking-tight leading-[1.1]">
              Stop arguing over architecture. <br />
              <span className="text-primary italic font-light">Start building.</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Initialize your workspace today and experience the smartest way to research engineering decisions.
            </p>
            <div className="pt-4">
              <Link 
                href="/workspaces"
                className="group relative inline-flex items-center justify-center gap-3 rounded-md bg-primary px-10 py-4 text-base font-semibold text-primary-foreground shadow-[0_0_40px_-10px_rgba(59,130,246,0.6)] hover:shadow-[0_0_80px_-10px_rgba(59,130,246,0.8)] hover:scale-[1.02] transition-all duration-500"
              >
                Initialize Workspace
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </main>
    </LandingLoaderWrapper>
  );
}
