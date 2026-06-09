import Link from "next/link";
import { ArrowRight, BrainCircuit, LineChart, FileDiff } from "lucide-react";
import Footer from "@/components/ui/Footer";
import SplitText from "@/components/SplitText";
import LightRays from "@/components/LightRays";
import CardSwap, { Card } from "@/components/CardSwap";
import GlassIcons from "@/components/GlassIcons";

export default function Home() {
  return (
    <div className="h-full w-full overflow-y-auto bg-background selection:bg-primary/30 relative">
      {/* Interactive WebGL Background */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-60 mix-blend-screen">
        <LightRays 
          raysOrigin="top-center" 
          raysColor="#3b82f6" // Primary blue
          mouseInfluence={0.05}
          lightSpread={1.2}
          raysSpeed={1.5}
        />
      </div>
      
      {/* Dark overlay to ensure text legibility */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/40 to-background pointer-events-none z-10" />

      <div className="flex flex-col min-h-full relative z-20">
        {/* Hero Section */}
        <section className="w-full min-h-[85vh] px-8 sm:px-12 md:px-16 lg:px-24 max-w-[100rem] mx-auto flex flex-col justify-center items-center text-center space-y-10 pt-20 pb-20 relative">
          
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-sm bg-surface/50 border border-white/10 backdrop-blur-md text-primary text-xs font-mono uppercase tracking-widest mb-4 shadow-2xl shadow-primary/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            SYSTEM.INIT(Atlas v1.0)
          </div>
          
          <div className="text-5xl md:text-7xl lg:text-[5rem] font-extrabold tracking-tighter text-foreground max-w-5xl leading-[1.05] drop-shadow-2xl">
            <SplitText 
              text="The smartest way to research system architecture." 
              className="text-center" 
              delay={35} 
              duration={1.2}
            />
          </div>
          
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-500 fill-mode-both font-medium">
            Stop guessing. Generate comprehensive decision documents, track architectural evolution, and compare tradeoffs instantly with AI.
          </p>

          <div className="pt-10 flex flex-col sm:flex-row items-center gap-6 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-700 fill-mode-both">
            <Link 
              href="/research"
              className="group relative inline-flex items-center justify-center gap-3 rounded-md bg-primary px-10 py-4 text-sm font-semibold text-primary-foreground shadow-[0_0_40px_-10px_rgba(59,130,246,0.6)] hover:shadow-[0_0_60px_-10px_rgba(59,130,246,0.8)] hover:scale-[1.02] transition-all duration-500"
            >
              Initialize Workspace
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
            </Link>
            <Link 
              href="/research-documents"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-surface/50 backdrop-blur-md px-10 py-4 text-sm font-mono text-foreground hover:bg-surface border border-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors duration-300"
            >
              [View_Examples]
            </Link>
          </div>
        </section>

        {/* Features Bento Grid */}
        <section className="w-full bg-transparent py-32 px-8 sm:px-12 md:px-16 lg:px-24 relative">
          <div className="absolute inset-0 bg-background/90 backdrop-blur-3xl -z-10 border-t border-white/5" />
          
          <div className="max-w-[100rem] mx-auto space-y-16 relative z-10">
            <div className="text-center space-y-4">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight drop-shadow-sm">Built for Engineering Excellence</h2>
              <p className="text-muted-foreground font-mono text-sm max-w-2xl mx-auto uppercase tracking-widest">
                // Core Capabilities
              </p>
            </div>

            <div className="flex justify-center items-center relative h-[500px] w-full max-w-4xl mx-auto">
              <CardSwap pauseOnHover={true} width={400} height={450} delay={4000}>
                {/* Feature 1 */}
                <Card className="flex flex-col items-center justify-center space-y-6 p-10 bg-surface/80 backdrop-blur-2xl border border-white/10 shadow-2xl">
                  <div className="absolute top-0 right-0 w-40 h-40 bg-primary/20 rounded-full blur-3xl -mr-20 -mt-20 opacity-50" />
                  <GlassIcons 
                    className="!flex !py-0 !gap-0 !my-0 items-center justify-center" 
                    items={[{ icon: <BrainCircuit className="w-8 h-8 text-white" />, color: 'blue', label: 'AI Deep Dives' }]} 
                  />
                  <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4">
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
                  <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4">
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
                  <p className="text-muted-foreground leading-relaxed text-center text-lg mt-4">
                    Compare saved research sessions side-by-side to understand exactly what changed between two approaches.
                  </p>
                </Card>
              </CardSwap>
            </div>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
}
