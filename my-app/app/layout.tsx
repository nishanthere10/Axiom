import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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

export const metadata: Metadata = {
  title: "Atlas Research",
  description: "AI-powered research workspace for software engineers.",
};

import Navbar from "@/components/ui/Navbar";
import { SystemStatusBanner } from "@/components/system/SystemStatusBanner";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html
        lang="en"
        className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
      >
        <body className="h-screen w-screen overflow-hidden flex flex-col" suppressHydrationWarning>
          <Navbar />
          <SystemStatusBanner />
          <main className="flex-1 overflow-hidden flex">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
