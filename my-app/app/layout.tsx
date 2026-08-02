import type { Metadata } from "next";
import { Geist, Geist_Mono, Plus_Jakarta_Sans } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Atlas Research — AI Architectural Decision Engine",
  description: "Generate comprehensive decision documents, compare architectural tradeoffs, and build persistent engineering memory with AI.",
  openGraph: {
    title: "Atlas Research — AI Architectural Decision Engine",
    description: "AI-powered research workspace for software engineers.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Atlas Research",
    description: "AI-powered research workspace for software engineers.",
  },
};

import Navbar from "@/components/ui/Navbar";
import { SystemStatusBanner } from "@/components/system/SystemStatusBanner";
import CommandPalette from "@/components/ui/CommandPalette";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { WorkspaceProvider } from "@/components/WorkspaceContext";

import { TooltipProvider } from "@/components/ui/tooltip";
import { Agentation } from 'agentation';
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <WorkspaceProvider>
        <ToastProvider>
          <TooltipProvider>
            <html
              lang="en"
              className={`${geistSans.variable} ${geistMono.variable} ${plusJakartaSans.variable} h-full antialiased dark`}
            >
              <body className="h-screen w-screen overflow-hidden flex flex-col" suppressHydrationWarning>
                <Agentation />
                <CommandPalette />
                <Navbar />
                <SystemStatusBanner />
                <main className="flex-1 overflow-hidden flex">{children}</main>
              </body>
            </html>
          </TooltipProvider>
        </ToastProvider>
      </WorkspaceProvider>
    </ClerkProvider>
  );
}
