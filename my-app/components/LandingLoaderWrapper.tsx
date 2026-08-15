"use client";

import { useState, useEffect } from "react";
import AxiomLoader from "@/components/landingpage-loader";

export default function LandingLoaderWrapper({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Artificial delay to show the SVG dash animation on initial load
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex h-screen w-full items-center justify-center bg-background">
        <AxiomLoader />
      </div>
    );
  }

  return <>{children}</>;
}
