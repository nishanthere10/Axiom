"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";

interface ExportButtonProps {
  sessionId: string;
  sessionType: "research" | "comparison";
}

export default function ExportButton({ sessionId, sessionType }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { getToken } = useAuth();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleExport = async (format: "markdown" | "adr" | "pdf") => {
    setIsOpen(false);
    setIsExporting(true);
    try {
      const token = await getToken();
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "https://atlas-1sr4.onrender.com";
      
      const response = await fetch(`${baseUrl}/export/${sessionType}/${sessionId}/${format}`, {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error("Export failed");
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `atlas-${sessionType}-${format}-${sessionId}.${format === 'pdf' ? 'pdf' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Failed to export document.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="no-print flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors rounded-md border border-border disabled:opacity-50"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 6 2 18 2 18 9"></polyline>
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
          <rect width="12" height="8" x="6" y="14"></rect>
        </svg>
        <span>{isExporting ? "Exporting..." : "Export"}</span>
      </button>
      
      {isOpen && (
        <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-popover ring-1 ring-border focus:outline-none z-50">
          <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
            <button
              onClick={() => handleExport("pdf")}
              className="block w-full text-left px-4 py-2 text-sm text-popover-foreground hover:bg-surface-hover"
              role="menuitem"
            >
              Professional PDF
            </button>
            <button
              onClick={() => handleExport("markdown")}
              className="block w-full text-left px-4 py-2 text-sm text-popover-foreground hover:bg-surface-hover"
              role="menuitem"
            >
              Markdown (.md)
            </button>
            <button
              onClick={() => handleExport("adr")}
              className="block w-full text-left px-4 py-2 text-sm text-popover-foreground hover:bg-surface-hover"
              role="menuitem"
            >
              Architecture Decision Record (ADR)
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
