import Link from "next/link";
import { ArrowRight, Box, ShieldCheck, Zap, Layers, RefreshCcw } from "lucide-react";
import Footer from "@/components/ui/Footer";
import DarkVeil from "@/components/DarkVeil";
import HeroCards from "@/components/HeroCards";

export default function Home() {
  return (
    <div className="h-full w-full overflow-y-auto bg-background selection:bg-primary/30 relative font-sans">
      {/* Interactive WebGL Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-50 mix-blend-screen h-[120vh]">
        <DarkVeil 
          hueShift={215} 
          noiseIntensity={0.05}
          scanlineIntensity={0.15}
          speed={0.4}
          scanlineFrequency={800}
          warpAmount={0.02}
        />
      </div>
      
      {/* Dark overlays to blend the background smoothly into the page content below */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/60 to-background pointer-events-none z-10 h-[120vh]" />

      <div className="flex flex-col min-h-full relative z-20">
        
        {/* =========================================
            HERO SECTION
           ========================================= */}
        <section className="w-full min-h-[90vh] px-8 sm:px-12 md:px-20 lg:px-32 max-w-[120rem] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center py-24 lg:py-32 relative">
          
          {/* Left Column: Text Content - Forced symmetrical height */}
          <div className="flex flex-col justify-center items-start text-left space-y-8 max-w-2xl h-[500px] w-full">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-surface/50 border border-white/10 backdrop-blur-md text-primary text-xs font-mono uppercase tracking-widest shadow-2xl shadow-primary/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              SYSTEM.INIT(Atlas v1.0)
            </div>
            
            {/* Display font used for maximum impact */}
            <h1 className="text-5xl md:text-6xl lg:text-[4.5rem] font-display font-bold tracking-tight text-foreground leading-[1.1] drop-shadow-2xl">
              The smartest way to research <br />
              <span className="font-mono text-primary font-light tracking-tight italic">
                system architecture.
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground animate-in fade-in slide-in-from-bottom-8 duration-700 delay-500 fill-mode-both font-medium">
              Stop guessing. Generate comprehensive decision documents, track architectural evolution, and compare tradeoffs instantly with AI.
            </p>

            <div className="pt-6 flex flex-col sm:flex-row items-center gap-6 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-700 fill-mode-both">
              <Link 
                href="/research"
                className="group relative inline-flex items-center justify-center gap-3 rounded-md bg-primary px-8 py-3.5 text-sm font-semibold text-primary-foreground shadow-[0_0_40px_-10px_rgba(59,130,246,0.6)] hover:shadow-[0_0_60px_-10px_rgba(59,130,246,0.8)] hover:scale-[1.02] transition-all duration-500"
              >
                Initialize Workspace
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </Link>
              <Link 
                href="/research-documents"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-surface/50 backdrop-blur-md px-8 py-3.5 text-sm font-mono text-foreground hover:bg-surface border border-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors duration-300"
              >
                [View_Examples]
              </Link>
            </div>
          </div>

          {/* Right Column: CardSwap - Forced symmetrical height */}
          <div className="relative w-full h-[500px] flex flex-col justify-center items-center animate-in fade-in zoom-in-95 duration-1000 delay-300 fill-mode-both">
            <HeroCards />
          </div>
        </section>

        {/* =========================================
            HOW IT WORKS SECTION 
           ========================================= */}
        <section className="w-full bg-surface/30 border-y border-white/5 py-32 px-8 sm:px-12 md:px-20 lg:px-32">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="text-center space-y-4">
              <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight">How Atlas Works</h2>
              <p className="text-primary font-mono text-sm uppercase tracking-widest">// The Research Pipeline</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
              {/* Connector line for desktop */}
              <div className="hidden md:block absolute top-1/2 left-0 right-0 h-px bg-white/10 -translate-y-1/2 z-0" />
              
              {/* Step 1 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-background border border-white/5 rounded-xl hover:border-primary/50 transition-colors group shadow-xl">
                <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500">
                  <Box className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">1. Define Context</h3>
                <p className="text-muted-foreground text-sm">
                  Input your architectural problem. Atlas identifies constraints, non-functional requirements, and edge cases.
                </p>
              </div>

              {/* Step 2 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-background border border-white/5 rounded-xl hover:border-primary/50 transition-colors group shadow-xl">
                <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500 delay-100">
                  <RefreshCcw className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">2. AI Decomposition</h3>
                <p className="text-muted-foreground text-sm">
                  Atlas runs deep literature reviews, compares database schemas, caching layers, and deployment strategies.
                </p>
              </div>

              {/* Step 3 */}
              <div className="relative z-10 flex flex-col items-center text-center space-y-4 p-8 bg-background border border-white/5 rounded-xl hover:border-primary/50 transition-colors group shadow-xl">
                <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-500 delay-200">
                  <Zap className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground font-display">3. Decision Output</h3>
                <p className="text-muted-foreground text-sm">
                  A fully formatted Markdown document with trust scores, alternatives evaluated, and a final recommendation.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* =========================================
            FEATURE ARSENAL (BENTO GRID)
           ========================================= */}
        <section className="w-full py-32 px-8 sm:px-12 md:px-20 lg:px-32">
          <div className="max-w-[100rem] mx-auto space-y-16">
            <div className="text-left space-y-4">
              <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight">Feature Arsenal</h2>
              <p className="text-primary font-mono text-sm uppercase tracking-widest">// Enterprise Grade Tools</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[300px]">
              
              {/* Bento Item 1: Large */}
              <div className="lg:col-span-2 relative group overflow-hidden rounded-2xl bg-surface border border-white/5 p-10 flex flex-col justify-end hover:border-primary/50 transition-all shadow-xl">
                <div className="absolute inset-0 bg-gradient-to-t from-background/90 to-transparent z-10" />
                <div className="absolute top-8 right-8 text-white/10 group-hover:text-primary/20 transition-colors">
                  <Layers className="w-48 h-48" />
                </div>
                <div className="relative z-20 space-y-3">
                  <h3 className="text-2xl font-bold font-display">Versioned Memory Panel</h3>
                  <p className="text-muted-foreground max-w-md">
                    Never lose context. Atlas remembers every architecture decision made in the past, allowing you to branch off previous designs or reference historical tradeoffs.
                  </p>
                </div>
              </div>

              {/* Bento Item 2: Small */}
              <div className="relative group overflow-hidden rounded-2xl bg-surface border border-white/5 p-10 flex flex-col justify-end hover:border-emerald-500/50 transition-all shadow-xl">
                <div className="absolute top-8 right-8 text-white/10 group-hover:text-emerald-500/20 transition-colors">
                  <ShieldCheck className="w-32 h-32" />
                </div>
                <div className="relative z-20 space-y-3">
                  <h3 className="text-2xl font-bold font-display">Trust Scoring</h3>
                  <p className="text-muted-foreground">
                    Every AI recommendation is paired with a transparent confidence metric so you know exactly when to trust it.
                  </p>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
}
