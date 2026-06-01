import MemoryPanel from "@/components/memory/MemoryPanel";
import ResizableLayout from "@/components/ui/ResizableLayout";

export default function MemoryPage() {
  return (
    <ResizableLayout>
      <div className="flex-1 overflow-y-auto p-4 md:p-8 relative">
        {/* Simple background effect similar to research page */}
        <div className="absolute inset-0 bg-gradient-to-tr from-background via-background to-secondary/10 -z-10" />
        <MemoryPanel />
      </div>
    </ResizableLayout>
  );
}
