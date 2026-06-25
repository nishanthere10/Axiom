"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased min-h-screen flex items-center justify-center">
        <div className="w-full max-w-md p-8 rounded-2xl border border-destructive/20 bg-destructive/5 text-center space-y-6">
          <div className="w-16 h-16 bg-destructive/10 border border-destructive/20 text-destructive rounded-full flex items-center justify-center mx-auto mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          
          <div>
            <h2 className="text-2xl font-semibold tracking-tight mb-2">Fatal Application Error</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              A critical failure occurred at the layout level. The application could not recover.
            </p>
          </div>

          <div className="pt-4">
            <button
              onClick={() => reset()}
              className="w-full inline-flex items-center justify-center rounded-xl text-sm font-medium transition-colors h-11 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
            >
              Force Restart
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
