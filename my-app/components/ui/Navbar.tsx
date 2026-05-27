import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 md:px-8">
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold sm:inline-block">Atlas Research</span>
          </Link>
          <div className="flex gap-4 md:gap-6">
            <Link
              href="/"
              className="text-sm font-medium transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Research
            </Link>
            <Link
              href="/compare"
              className="text-sm font-medium transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Compare
            </Link>
            <Link
              href="/compare/saved"
              className="text-sm font-medium transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Saved Comparisons
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
