import Link from "next/link";
import { Code, Globe, MessageCircle } from "lucide-react"; // Using generic icons since brands were removed

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-border/50 bg-background py-8 md:py-12 mt-auto">
      <div className="container px-4 md:px-6 mx-auto max-w-7xl flex flex-col md:flex-row justify-between items-center gap-6">
        {/* Left Side: Brand & Copyright */}
        <div className="flex flex-col items-center md:items-start gap-2">
          <Link href="/" className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight">Atlas Research</span>
          </Link>
          <p className="text-xs text-muted-foreground">
            &copy; {currentYear} Atlas. All rights reserved.
          </p>
        </div>

        {/* Center: Secondary Links */}
        <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground font-medium">
          <Link href="/research" className="hover:text-foreground transition-colors">
            App
          </Link>
          <Link href="/research-documents" className="hover:text-foreground transition-colors">
            Docs
          </Link>
          <Link href="/compare" className="hover:text-foreground transition-colors">
            Compare
          </Link>
          <Link href="#" className="hover:text-foreground transition-colors">
            Terms
          </Link>
          <Link href="#" className="hover:text-foreground transition-colors">
            Privacy
          </Link>
        </div>

        {/* Right Side: Socials */}
        <div className="flex items-center gap-4 text-muted-foreground">
          <Link href="#" className="hover:text-foreground transition-colors" aria-label="GitHub">
            <Code className="w-5 h-5" />
          </Link>
          <Link href="#" className="hover:text-foreground transition-colors" aria-label="Twitter">
            <Globe className="w-5 h-5" />
          </Link>
          <Link href="#" className="hover:text-foreground transition-colors" aria-label="Reddit / Community">
            <MessageCircle className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </footer>
  );
}
