export default function VerdictBanner({ verdict }: { verdict: string }) {
  if (!verdict) return null;
  
  return (
    <div className="bg-primary/10 border-l-4 border-primary p-6 rounded-r-md">
      <h2 className="text-xl font-bold text-foreground leading-snug">
        {verdict}
      </h2>
    </div>
  );
}
