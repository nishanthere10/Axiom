import MemoryPanel from "@/components/features/MemoryPanel";

export default function MemoryPage() {
  return (
    <div className="flex flex-col h-[100vh] w-full overflow-hidden bg-background">
      {/* Background gradients */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[80px] bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2" />
      </div>

      <MemoryPanel />
    </div>
  );
}
