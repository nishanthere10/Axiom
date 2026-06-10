import Link from "next/link";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-border/50 bg-background py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">

        {/* Brand */}
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
          <Link href="/" className="font-semibold text-foreground tracking-tight hover:text-foreground/80 transition-colors">
            Atlas Research
          </Link>
          <span className="text-border">·</span>
          <span>&copy; {currentYear}</span>
        </div>

        {/* Nav links */}
        <div className="flex items-center gap-5 font-mono">
          {[
            { href: "/research",           label: "App" },
            { href: "/research-documents", label: "Docs" },
            { href: "/compare",            label: "Compare" },
          ].map(({ href, label }) => (
            <Link key={href} href={href} className="hover:text-foreground transition-colors">
              {label}
            </Link>
          ))}
        </div>

      </div>
    </footer>
  );
}
