"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SignInButton,
  UserButton,
  useAuth,
} from "@clerk/nextjs";
import { Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import WorkspaceSelector from "@/components/WorkspaceSelector";

const NAV_LINKS = [
  { href: "/research",           label: "Research",          exact: false },
  { href: "/research-documents", label: "Saved Research",     exact: true  },
  { href: "/compare",            label: "Compare",           exact: true  },
  { href: "/compare/saved",      label: "Saved Comparisons", exact: true  },
];

export default function Navbar() {
  const { isSignedIn } = useAuth();
  const pathname = usePathname();

  return (
    <nav className="relative z-50 shrink-0 border-b border-border bg-surface/80 backdrop-blur-md supports-[backdrop-filter]:bg-surface/60">
      <div className="flex h-16 items-center justify-between px-4 md:px-8">

        {/* Left: Brand + Nav Links */}
        <div className="flex items-center gap-6">
          <Link
            href="/"
            className="flex items-center gap-2.5 text-base font-semibold text-foreground tracking-tight hover:text-foreground/80 transition-colors"
          >
            {/* Subtle accent dot */}
            <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
            Atlas Research
          </Link>

          {isSignedIn && (
            <div className="hidden md:block ml-4">
              <WorkspaceSelector />
            </div>
          )}

          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(({ href, label, exact }) => {
              const isActive = exact
                ? pathname === href
                : pathname === href || pathname?.startsWith(href + "?") || pathname?.startsWith(href + "/");
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "relative px-4 py-2 rounded-md text-sm font-medium transition-all duration-200",
                    isActive
                      ? "text-foreground bg-surface-hover"
                      : "text-muted-foreground hover:text-foreground hover:bg-surface-hover/60"
                  )}
                >
                  {label}
                  {isActive && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-px bg-primary rounded-full" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right: Auth */}
        <div className="flex items-center gap-4">
          {isSignedIn ? (
            <>
              <UserButton 
                appearance={{
                  elements: {
                    userButtonAvatarBox: "w-8 h-8 rounded-md border border-border"
                  }
                }}
              />
            </>
          ) : (
            <SignInButton>
              <button className="inline-flex items-center justify-center rounded-md text-xs font-semibold transition-colors h-8 px-3 bg-primary text-primary-foreground hover:bg-primary/90">
                Sign In
              </button>
            </SignInButton>
          )}
        </div>

      </div>
    </nav>
  );
}
