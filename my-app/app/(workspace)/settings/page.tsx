"use client";

import Link from "next/link";
import { BrainCircuit, Settings } from "lucide-react";
import { useWorkspace } from "@/components/WorkspaceContext";

// Custom Github SVG icon
function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.02c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A4.8 4.8 0 0 0 8 18v4" />
    </svg>
  );
}

export default function SettingsPage() {
  const { activeWorkspaceId } = useWorkspace();

  return (
    <div className="relative w-full min-h-[calc(100vh-8rem)] flex flex-col pt-12 md:pt-20 max-w-4xl mx-auto px-6 space-y-8">
      <div className="absolute inset-0 -z-10 flex items-center justify-center pointer-events-none">
        <div className="absolute w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px]" />
        <div className="absolute w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[80px] translate-x-1/4 -translate-y-1/4" />
      </div>

      <div className="mb-10 text-center md:text-left">
        <h1 className="text-3xl md:text-4xl font-medium tracking-tight text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-2">Manage your Atlas preferences, integrations, and memory.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link href="/settings/integrations/github" className="group p-6 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-border/80 hover:bg-surface/80 hover:-translate-y-1 hover:shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all duration-300">
          <div className="w-12 h-12 rounded-full bg-surface/50 border border-border/40 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 shadow-sm">
            <GithubIcon className="w-6 h-6 text-foreground group-hover:text-primary transition-colors" />
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground mb-2">GitHub Integration</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Connect your repositories so Atlas can understand your architecture, stack, and context without indexing source code.
          </p>
        </Link>

        <Link href="/memory" className="group p-6 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-border/80 hover:bg-surface/80 hover:-translate-y-1 hover:shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all duration-300">
          <div className="w-12 h-12 rounded-full bg-surface/50 border border-border/40 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 shadow-sm">
            <BrainCircuit className="w-6 h-6 text-foreground group-hover:text-primary transition-colors" />
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground mb-2">Atlas Memory</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Manage your persistent project context, learned constraints, and structural memories that guide architectural decisions.
          </p>
        </Link>

        {activeWorkspaceId && (
          <Link href={`/workspaces/${activeWorkspaceId}`} className="group p-6 rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-border/80 hover:bg-surface/80 hover:-translate-y-1 hover:shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all duration-300">
            <div className="w-12 h-12 rounded-full bg-surface/50 border border-border/40 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 shadow-sm">
              <Settings className="w-6 h-6 text-foreground group-hover:text-primary transition-colors" />
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-foreground mb-2">Workspace Stats</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              View your active workspace's analytics, team members, and comprehensive operational metrics.
            </p>
          </Link>
        )}
      </div>
    </div>
  );
}
