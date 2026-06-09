"use client";

import Link from "next/link";
import {
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/nextjs";

export default function Navbar() {
  return (
    <nav className="border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4 md:px-8">
        {/* Left: Brand + Nav Links */}
        <div className="flex items-center">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold sm:inline-block">Atlas Research</span>
          </Link>
          <div className="flex gap-4 md:gap-6">
            <Link
              href="/research"
              className="text-sm font-medium transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Research
            </Link>
            <Link
              href="/research-documents"
              className="text-sm font-medium transition-colors hover:text-foreground/80 text-foreground/60"
            >
              Saved Research
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

        {/* Right: Auth */}
        <div className="flex items-center gap-3">
          <SignedIn>
            <UserButton
              afterSignOutUrl="/"
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8",
                },
              }}
            />
          </SignedIn>
          <SignedOut>
            <Link
              href="/sign-in"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-9 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Sign In
            </Link>
          </SignedOut>
        </div>
      </div>
    </nav>
  );
}
