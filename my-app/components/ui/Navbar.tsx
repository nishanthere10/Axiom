"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SignInButton,
  UserButton,
  useAuth,
} from "@clerk/nextjs";
import { Settings, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import WorkspaceSelector from "@/components/WorkspaceSelector";
import { useWorkspace } from "@/components/WorkspaceContext";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const NAV_LINKS = [
  { href: "/research",           label: "Research",          exact: false },
  { href: "/research-documents", label: "Saved Research",     exact: true  },
  { href: "/compare",            label: "Compare",           exact: true  },
  { href: "/compare/saved",      label: "Saved Comparisons", exact: true  },
  { href: "/memory",             label: "Memory",            exact: true  },
];

export default function Navbar() {
  const { isSignedIn } = useAuth();
  const pathname = usePathname();
  const { activeWorkspaceId } = useWorkspace();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="relative z-50 shrink-0 border-b border-border bg-surface/80 backdrop-blur-md supports-[backdrop-filter]:bg-surface/60">
      <div className="flex h-16 items-center justify-between px-4 md:px-8">

        {/* Left: Brand + Nav Links */}
        <div className="flex items-center gap-4 md:gap-6">
          {/* Mobile Sheet Trigger */}
          <div className="flex md:hidden">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <button
                  aria-label="Open Navigation Menu"
                  className="p-2 rounded-md hover:bg-surface-hover text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none"
                >
                  <Menu className="w-5 h-5" />
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="bg-surface border-border text-foreground p-6">
                <SheetHeader className="text-left mb-6">
                  <SheetTitle className="text-base font-semibold flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary" />
                    Atlas Research
                  </SheetTitle>
                </SheetHeader>

                {isSignedIn && (
                  <div className="mb-6">
                    <WorkspaceSelector />
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  {NAV_LINKS.map(({ href, label, exact }) => {
                    const fullHref = activeWorkspaceId ? `/workspaces/${activeWorkspaceId}${href}` : "/workspaces";
                    const isActive = exact
                      ? pathname === fullHref
                      : pathname === fullHref || pathname?.startsWith(fullHref + "?") || pathname?.startsWith(fullHref + "/");
                    return (
                      <Link
                        key={href}
                        href={fullHref}
                        onClick={() => setMobileOpen(false)}
                        className={cn(
                          "px-4 py-2.5 rounded-lg text-sm font-medium transition-colors",
                          isActive
                            ? "text-primary bg-primary/10"
                            : "text-muted-foreground hover:text-foreground hover:bg-surface-hover",
                          !activeWorkspaceId && "opacity-50 pointer-events-none"
                        )}
                      >
                        {label}
                      </Link>
                    );
                  })}

                  {activeWorkspaceId && (
                    <Link
                      href={`/workspaces/${activeWorkspaceId}/settings`}
                      onClick={() => setMobileOpen(false)}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors mt-4 border-t border-border/50 pt-4"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </Link>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>

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
              const fullHref = activeWorkspaceId ? `/workspaces/${activeWorkspaceId}${href}` : "/workspaces";
              const isActive = exact
                ? pathname === fullHref
                : pathname === fullHref || pathname?.startsWith(fullHref + "?") || pathname?.startsWith(fullHref + "/");
              return (
                <Link
                  key={href}
                  href={fullHref}
                  className={cn(
                    "relative px-4 py-2 rounded-md text-sm font-medium transition-all duration-200",
                    isActive
                      ? "text-foreground bg-surface-hover"
                      : "text-muted-foreground hover:text-foreground hover:bg-surface-hover/60",
                    !activeWorkspaceId && "opacity-50 pointer-events-none"
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

        {/* Right: Auth & Settings */}
        <div className="flex items-center gap-3">
          {isSignedIn && activeWorkspaceId && (
            <Link
              href={`/workspaces/${activeWorkspaceId}/settings`}
              aria-label="Workspace Settings"
              className="hidden md:flex items-center justify-center p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-surface-hover focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none transition-colors"
            >
              <Settings className="w-4 h-4" />
            </Link>
          )}

          {isSignedIn ? (
            <UserButton 
              appearance={{
                elements: {
                  userButtonAvatarBox: "w-8 h-8 rounded-md border border-border"
                }
              }}
            />
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
