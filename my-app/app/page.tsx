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
      <div className="fixed inset-0 bg-zinc-950 z-0" />
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden opacity-40">
        <Aurora 
          colorStops={["#020617", "#1e3a8a", "#2563eb", "#38bdf8", "#00f2fe"]} 
          amplitude={1.6}
          blend={0.85}
          speed={0.5}
        />
      </div>
      <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.15),rgba(255,255,255,0))]" />

      <div className="flex flex-col min-h-full relative z-20">
        
        {/* =========================================
            HERO SECTION
           ========================================= */}
        <header className="w-full min-h-[85vh] px-10 sm:px-16 md:px-24 lg:px-48 max-w-[100rem] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center py-24 lg:py-36 relative">

          {/* Left Column: Text Content */}
          <div className="flex flex-col items-start text-left space-y-8">

            <h1 className="text-5xl md:text-6xl lg:text-[4.5rem] font-sans font-semibold tracking-tighter text-zinc-100 leading-[1.05]">
              The smartest way to research <br className="hidden lg:block" />
              <span className="font-sans font-normal italic text-zinc-400">
                system architecture.
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-zinc-400 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-500 fill-mode-both font-normal">
              Stop guessing. Generate comprehensive decision documents, track architectural evolution, and compare tradeoffs instantly with AI.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-start gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-700 fill-mode-both">
              <Link 
                href="/workspaces"
                className="group relative inline-flex h-11 items-center justify-center gap-2 rounded-md bg-zinc-100 px-6 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-300 active:scale-95"
              >
                Initialize Workspace
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-300" />
              </Link>
              <Link 
                href="/research-documents"
                className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-zinc-900 px-6 text-sm font-medium text-zinc-300 transition-colors border border-zinc-800 hover:bg-zinc-800 hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring active:scale-95"
              >
                View Examples
              </Link>
            </div>
          </div>

          {/* Right Column: HeroCards */}
          <div className="hidden lg:block relative w-full min-h-[520px] animate-in fade-in zoom-in-95 duration-1000 delay-300 fill-mode-both">
            <HeroCards />
          </div>
        </header>



        {/* =========================================
            HOW IT WORKS SECTION 
           ========================================= */}
        <section aria-label="How it works" className="w-full py-24 px-10 sm:px-16 md:px-24 lg:px-48 border-t border-zinc-900">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <h2 className="text-3xl font-sans font-medium tracking-tight text-zinc-100">How Axiom Works</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
              {/* Step 1 */}
              <div className="flex flex-col space-y-4 p-8 bg-zinc-900/50 border border-zinc-800/50 rounded-xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-100">
                <div className="w-10 h-10 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/50 text-zinc-300">
                  <Box className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-medium text-zinc-100">Define Decision</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Input your architectural dilemma. Axiom decomposes the problem into research axes and identifies constraints.
                </p>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col space-y-4 p-8 bg-zinc-900/50 border border-zinc-800/50 rounded-xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
                <div className="w-10 h-10 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/50 text-zinc-300">
                  <RefreshCcw className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-medium text-zinc-100">Evidence Synthesis</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Runs 8 parallel research nodes — memory graph search, codebase indexing, web evidence scoring, and contradiction detection.
                </p>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col space-y-4 p-8 bg-zinc-900/50 border border-zinc-800/50 rounded-xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
                <div className="w-10 h-10 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700/50 text-zinc-300">
                  <Zap className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-medium text-zinc-100">Decision Record</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  Delivers a complete decision document: recommendation, tradeoff matrix, confidence breakdown, and Mermaid diagrams.
                </p>
              </div>
            </div>



          </div>
        </section>

        {/* =========================================
            FEATURE ARSENAL (BENTO GRID)
           ========================================= */}
        <section aria-label="Feature Arsenal" className="w-full py-24 px-10 sm:px-16 md:px-24 lg:px-48 bg-zinc-950/40 backdrop-blur-md">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="text-left space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <h2 className="text-3xl font-sans font-medium tracking-tight text-zinc-100">Feature Arsenal</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
              
              {/* Bento Item 1 */}
              <div className="relative group overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 p-6 flex flex-col justify-end hover:border-zinc-700 hover:-translate-y-0.5 transition-all duration-300 min-h-[200px]">
                <div className="absolute top-6 right-6 text-zinc-800 group-hover:text-zinc-700 transition-colors z-0">
                  <Layers className="w-24 h-24" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-medium text-zinc-100">Versioned Memory Graph</h3>
                  <p className="text-zinc-400 text-sm max-w-md">
                    Axiom extracts and remembers historical decisions, team preferences, and constraints across sessions to build persistent context.
                  </p>
                </div>
              </div>

              {/* Bento Item 2 */}
              <div className="relative group overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 p-8 flex flex-col justify-end hover:border-zinc-700 hover:-translate-y-0.5 transition-all duration-300 min-h-[260px]">
                <div className="absolute top-6 right-6 text-zinc-800 group-hover:text-zinc-700 transition-colors z-0">
                  <ShieldCheck className="w-24 h-24" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-medium text-zinc-100">Trust Scoring</h3>
                  <p className="text-zinc-400 text-sm">
                    4-axis transparent confidence scoring for source quality, coverage, contradiction risk, and overall decision strength.
                  </p>
                </div>
              </div>

              {/* Bento Item 3 */}
              <div className="relative group overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 p-8 flex flex-col justify-end hover:border-zinc-700 hover:-translate-y-0.5 transition-all duration-300 min-h-[260px]">
                <div className="absolute top-6 right-6 text-zinc-800 group-hover:text-zinc-700 transition-colors z-0">
                  <Scale className="w-24 h-24" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-medium text-zinc-100">Compare Engine</h3>
                  <p className="text-zinc-400 text-sm">
                    Side-by-side structural comparison of two past research sessions to highlight tradeoffs and metric diffs.
                  </p>
                </div>
              </div>

              {/* Bento Item 4 */}
              <div className="relative group overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 p-8 flex flex-col justify-end hover:border-zinc-700 hover:-translate-y-0.5 transition-all duration-300 min-h-[260px]">
                <div className="absolute top-6 right-6 text-zinc-800 group-hover:text-zinc-700 transition-colors z-0">
                  <GitBranch className="w-24 h-24" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-medium text-zinc-100">Codebase Context</h3>
                  <p className="text-zinc-400 text-sm">
                    Indexes your GitHub repo structure and doc files to evaluate choices against your actual codebase architecture.
                  </p>
                </div>
              </div>

              {/* Bento Item 5 */}
              <div className="relative group overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 p-6 flex flex-col justify-end hover:border-zinc-700 hover:-translate-y-0.5 transition-all duration-300 min-h-[200px]">
                <div className="absolute top-6 right-6 text-zinc-800 group-hover:text-zinc-700 transition-colors z-0">
                  <Network className="w-24 h-24" />
                </div>
                <div className="relative z-20 space-y-2">
                  <h3 className="text-xl font-medium text-zinc-100">Auto Diagram Specs</h3>
                  <p className="text-zinc-400 text-sm max-w-md">
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
        <section aria-label="Get Started CTA" className="w-full py-32 px-10 sm:px-16 md:px-24 lg:px-48 border-t border-zinc-900 relative overflow-hidden bg-zinc-950/40 backdrop-blur-md">
          
          <div className="max-w-4xl mx-auto relative z-10 text-center space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <h2 className="text-4xl md:text-5xl font-sans font-medium tracking-tight leading-[1.1] text-zinc-100">
              Stop arguing over architecture. <br />
              <span className="text-zinc-500 font-normal">Start building.</span>
            </h2>
            <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
              Initialize your workspace today and experience the smartest way to research engineering decisions.
            </p>
            <div className="pt-8 flex justify-center">
              <Link 
                href="/workspaces"
                className="group relative inline-flex h-11 items-center justify-center gap-2 rounded-md bg-zinc-100 px-8 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-300 active:scale-95"
              >
                Initialize Workspace
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform duration-300" />
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
