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
  title: "Atlas Research",
  description: "AI-powered research workspace for software engineers.",
};

import Navbar from "@/components/ui/Navbar";
import { SystemStatusBanner } from "@/components/system/SystemStatusBanner";
import CommandPalette from "@/components/ui/CommandPalette";
import { ToastProvider } from "@/components/ui/ToastProvider";
import { WorkspaceProvider } from "@/components/WorkspaceContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <WorkspaceProvider>
        <ToastProvider>
          <html
        lang="en"
        className={`${geistSans.variable} ${geistMono.variable} ${plusJakartaSans.variable} h-full antialiased dark`}
      >
        <body className="h-screen w-screen overflow-hidden flex flex-col" suppressHydrationWarning>
          <CommandPalette />
          <Navbar />
          <SystemStatusBanner />
          <main className="flex-1 overflow-hidden flex">{children}</main>
        </body>
          </html>
        </ToastProvider>
      </WorkspaceProvider>
    </ClerkProvider>
  );
}
