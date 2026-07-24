import Loader from "@/components/main-loader";

export default function Loading() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <Loader />
    </div>
  );
}
