import Link from "next/link";
import { Search, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-6">
      <div className="absolute inset-0 -z-10 flex items-center justify-center pointer-events-none">
        <div className="absolute w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px]" />
      </div>

      <div className="w-full max-w-md p-10 rounded-3xl border border-border/60 bg-surface/40 backdrop-blur-md shadow-2xl text-center space-y-6">
        <div className="w-20 h-20 bg-surface/80 border border-border/40 text-muted-foreground rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm relative overflow-hidden">
          <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity" />
          <Search className="w-8 h-8" />
        </div>
        
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground mb-3">404</h1>
          <h2 className="text-xl font-medium tracking-tight text-foreground mb-2">Page Not Found</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-[250px] mx-auto">
            We couldn't find the page or workspace you're looking for. It might have been moved or deleted.
          </p>
        </div>

        <div className="pt-6">
          <Link
            href="/workspaces"
            className="w-full inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors h-12 bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg hover:-translate-y-0.5 duration-300"
          >
            <Home className="w-4 h-4" /> Go to Workspaces
          </Link>
        </div>
      </div>
    </div>
  );
}
