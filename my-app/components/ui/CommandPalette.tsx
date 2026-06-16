"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Search, FileText, GitCompare, BookOpen, Settings } from "lucide-react";

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle on Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen((open) => !open);
      }
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const runCommand = (command: () => void) => {
    setIsOpen(false);
    command();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh]">
          {/* Backdrop Blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Command Palette Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="relative w-full max-w-xl mx-4 bg-surface border border-border shadow-2xl rounded-xl overflow-hidden"
          >
            <div className="flex items-center border-b border-border px-4">
              <Search className="w-5 h-5 text-muted-foreground mr-3 shrink-0" />
              <input
                autoFocus
                className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground py-4 focus:outline-none"
                placeholder="Type a command or search..."
              />
              <div className="text-[10px] text-muted-foreground font-mono bg-surface-hover px-1.5 py-0.5 rounded border border-border/50">
                ESC
              </div>
            </div>
            
            <div className="p-2 max-h-[350px] overflow-y-auto">
              <div className="text-xs font-semibold text-muted-foreground px-2 py-2 uppercase tracking-widest">
                Quick Navigation
              </div>
              
              <button
                onClick={() => runCommand(() => router.push("/research"))}
                className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm text-foreground hover:bg-surface-hover hover:text-primary transition-colors text-left"
              >
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span>New Research Session</span>
              </button>
              
              <button
                onClick={() => runCommand(() => router.push("/compare"))}
                className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm text-foreground hover:bg-surface-hover hover:text-primary transition-colors text-left"
              >
                <GitCompare className="w-4 h-4 text-muted-foreground" />
                <span>Compare Architectures</span>
              </button>
              
              <button
                onClick={() => runCommand(() => router.push("/memory"))}
                className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm text-foreground hover:bg-surface-hover hover:text-primary transition-colors text-left"
              >
                <BookOpen className="w-4 h-4 text-muted-foreground" />
                <span>View Global Memory & Context</span>
              </button>

              <button
                onClick={() => runCommand(() => router.push("/"))}
                className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-sm text-foreground hover:bg-surface-hover hover:text-primary transition-colors text-left"
              >
                <Settings className="w-4 h-4 text-muted-foreground" />
                <span>Back to Landing Page</span>
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
